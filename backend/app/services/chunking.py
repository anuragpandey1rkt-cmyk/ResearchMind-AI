from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import get_settings


class ChunkingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, text: str) -> list[str]:
        chunks = [chunk.strip() for chunk in self.splitter.split_text(text) if chunk.strip()]
        return chunks
