import hashlib
from functools import cached_property
from typing import Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self.settings.embedding_model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class ChromaVectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.embedding_service = EmbeddingService()
        self.documents = self.client.get_or_create_collection("research_documents")
        self.chunks = self.client.get_or_create_collection("research_chunks")
        self.paper_chunks = self.client.get_or_create_collection("paper_chunks")
        self.paper_metadata = self.client.get_or_create_collection("paper_metadata")
        self.research_findings = self.client.get_or_create_collection("research_findings")
        self.research_limitations = self.client.get_or_create_collection("research_limitations")
        self.future_work = self.client.get_or_create_collection("future_work")

    def add_chunks(self, chunks: list[str], metadata: dict[str, Any]) -> list[str]:
        if not chunks:
            return []
        embeddings = self.embedding_service.embed(chunks)
        ids = [
            hashlib.sha256(f"{metadata.get('document_id')}:{idx}:{chunk}".encode()).hexdigest()
            for idx, chunk in enumerate(chunks)
        ]
        metadatas = [{**metadata, "chunk_index": idx} for idx in range(len(chunks))]
        self.chunks.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        return ids

    def add_source_text(self, source_id: str, text: str, metadata: dict[str, Any]) -> None:
        embedding = self.embedding_service.embed([text[:4000]])[0]
        self.documents.upsert(ids=[source_id], embeddings=[embedding], documents=[text], metadatas=[metadata])

    def query(self, query: str, top_k: int = 8, session_id: str | None = None) -> list[dict[str, Any]]:
        embedding = self.embedding_service.embed([query])[0]
        where = {"session_id": session_id} if session_id else None
        result = self.chunks.query(query_embeddings=[embedding], n_results=top_k, where=where)
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        rows: list[dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            rows.append(
                {
                    "id": ids[idx],
                    "text": doc,
                    "metadata": metadatas[idx] or {},
                    "score": float(1 - distances[idx]) if idx < len(distances) else 0.0,
                }
            )
        return rows

    def add_paper_artifacts(self, paper: dict, chunks: list[str]) -> None:
        document_id = paper["document_id"]
        if chunks:
            embeddings = self.embedding_service.embed(chunks)
            ids = [f"paper_chunk:{document_id}:{idx}" for idx in range(len(chunks))]
            metadatas = [
                {
                    "document_id": document_id,
                    "filename": paper.get("filename", ""),
                    "title": paper.get("title", ""),
                    "artifact_type": "paper_chunk",
                    "chunk_index": idx,
                }
                for idx in range(len(chunks))
            ]
            self.paper_chunks.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

        metadata_text = "\n".join(
            [
                paper.get("title", ""),
                "Authors: " + ", ".join(paper.get("authors", [])),
                "Areas: " + ", ".join(paper.get("research_areas", [])),
                "Methods: " + ", ".join(paper.get("methods", [])),
                "Datasets: " + ", ".join(paper.get("datasets", [])),
                "Metrics: " + ", ".join(paper.get("metrics", [])),
            ]
        )
        self._upsert_single(self.paper_metadata, f"paper_metadata:{document_id}", metadata_text, paper, "paper_metadata")
        self._upsert_list(self.research_findings, document_id, paper.get("key_findings", []), paper, "research_findings")
        self._upsert_list(self.research_limitations, document_id, paper.get("limitations", []), paper, "research_limitations")
        self._upsert_list(self.future_work, document_id, paper.get("future_work", []), paper, "future_work")

    def query_paper_collection(self, collection_name: str, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        collection = getattr(self, collection_name)
        embedding = self.embedding_service.embed([query])[0]
        result = collection.query(query_embeddings=[embedding], n_results=top_k)
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        return [
            {
                "id": ids[idx],
                "text": doc,
                "metadata": metadatas[idx] or {},
                "score": float(1 - distances[idx]) if idx < len(distances) else 0.0,
            }
            for idx, doc in enumerate(docs)
        ]

    def _upsert_list(self, collection, document_id: str, values: list[str], paper: dict, artifact_type: str) -> None:
        clean = [value for value in values if value.strip()]
        if not clean:
            return
        embeddings = self.embedding_service.embed(clean)
        ids = [f"{artifact_type}:{document_id}:{idx}" for idx in range(len(clean))]
        metadatas = [
            {
                "document_id": document_id,
                "filename": paper.get("filename", ""),
                "title": paper.get("title", ""),
                "artifact_type": artifact_type,
            }
            for _ in clean
        ]
        collection.upsert(ids=ids, embeddings=embeddings, documents=clean, metadatas=metadatas)

    def _upsert_single(self, collection, row_id: str, text: str, paper: dict, artifact_type: str) -> None:
        embedding = self.embedding_service.embed([text or paper.get("title", "Untitled paper")])[0]
        collection.upsert(
            ids=[row_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "document_id": paper.get("document_id", ""),
                    "filename": paper.get("filename", ""),
                    "title": paper.get("title", ""),
                    "artifact_type": artifact_type,
                }
            ],
        )
