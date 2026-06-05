import hashlib
from pathlib import Path
import fitz
import pdfplumber


class PdfService:
    def save_pdf(self, data: bytes, upload_dir: Path, filename: str) -> tuple[Path, str]:
        digest = hashlib.sha256(data).hexdigest()
        safe_name = "".join(char if char.isalnum() or char in ".-_" else "_" for char in filename)
        path = upload_dir / f"{digest[:16]}_{safe_name}"
        path.write_bytes(data)
        return path, digest

    def extract_text(self, path: Path) -> str:
        text_parts: list[str] = []
        try:
            with fitz.open(path) as document:
                for page in document:
                    text = page.get_text("text")
                    if text.strip():
                        text_parts.append(text)
        except Exception:
            text_parts = []

        if not "".join(text_parts).strip():
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        text_parts.append(text)
        return "\n\n".join(text_parts).strip()
