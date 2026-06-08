import hashlib
from pathlib import Path
import fitz
import pdfplumber
from supabase import create_client, Client
from app.core.config import get_settings


class PdfService:
    def __init__(self):
        self.settings = get_settings()
        self.supabase: Client = create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)

    def save_pdf(self, data: bytes, upload_dir: Path, filename: str) -> tuple[str, str]:
        digest = hashlib.sha256(data).hexdigest()
        safe_name = "".join(char if char.isalnum() or char in ".-_" else "_" for char in filename)
        storage_path = f"{digest[:16]}_{safe_name}"
        
        # Upload to Supabase Storage
        res = self.supabase.storage.from_(self.settings.supabase_bucket_name).upload(
            file=data,
            path=storage_path,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        
        # Get public URL
        public_url = self.supabase.storage.from_(self.settings.supabase_bucket_name).get_public_url(storage_path)
        
        return public_url, digest

    def extract_text(self, data: bytes) -> str:
        import io
        text_parts: list[str] = []
        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                for page in document:
                    text = page.get_text("text")
                    if text.strip():
                        text_parts.append(text)
        except Exception:
            text_parts = []

        if not "".join(text_parts).strip():
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        text_parts.append(text)
        return "\n\n".join(text_parts).strip()

    async def download_pdf(self, storage_path: str) -> bytes:
        import httpx
        if storage_path.startswith(("http://", "https://")):
            async with httpx.AsyncClient() as client:
                res = await client.get(storage_path)
                res.raise_for_status()
                return res.content
        else:
            path = Path(storage_path)
            if not path.is_absolute():
                path = Path(self.settings.upload_path) / path.name
            return path.read_bytes()
