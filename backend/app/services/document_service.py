from pathlib import Path
from app.core.config import get_settings
from app.repositories.research_repository import ResearchRepository
from app.services.chunking import ChunkingService
from app.services.pdf_service import PdfService
from app.services.vector_store import ChromaVectorStore


class DocumentService:
    def __init__(self, repo: ResearchRepository) -> None:
        self.repo = repo
        self.settings = get_settings()
        self.pdf_service = PdfService()
        self.chunker = ChunkingService()
        self.vector_store = ChromaVectorStore()

    async def ingest_pdf(
        self,
        data: bytes,
        filename: str,
        content_type: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ):
        public_url, digest = self.pdf_service.save_pdf(data, self.settings.upload_path, filename)
        text = self.pdf_service.extract_text(data)
        chunks = self.chunker.chunk(text)
        document = await self.repo.add_document(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            storage_path=public_url,
            document_hash=digest,
            extracted_chars=len(text),
            chunks_count=len(chunks),
        )
        self.vector_store.add_chunks(
            chunks,
            {
                "document_id": document.id,
                "session_id": session_id or "",
                "filename": filename,
                "document_hash": digest,
                "source_type": "pdf",
            },
        )
        return document
