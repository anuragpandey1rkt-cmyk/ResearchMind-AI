import hashlib
from functools import cached_property
from typing import Any
from pinecone import Pinecone
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self, pc: Pinecone) -> None:
        self.settings = get_settings()
        self.pc = pc

    def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.pc.inference.embed(
                model="multilingual-e5-large",
                inputs=batch,
                parameters={"input_type": "passage", "truncate": "END"}
            )
            results.extend([data.values for data in response.data])
        return results


class PineconeVectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index = self.pc.Index(self.settings.pinecone_index_name)
        self.embedding_service = EmbeddingService(self.pc)

    def add_chunks(self, chunks: list[str], metadata: dict[str, Any]) -> list[str]:
        if not chunks:
            return []
        embeddings = self.embedding_service.embed(chunks)
        ids = [
            hashlib.sha256(f"{metadata.get('document_id')}:{idx}:{chunk}".encode()).hexdigest()
            for idx, chunk in enumerate(chunks)
        ]
        
        vectors = []
        for idx, chunk in enumerate(chunks):
            # Pinecone metadata values must be strings, numbers, booleans, or lists of strings
            safe_metadata = {k: v for k, v in metadata.items() if v is not None}
            safe_metadata["chunk_index"] = idx
            safe_metadata["text"] = chunk # Store text in metadata to retrieve it
            vectors.append((ids[idx], embeddings[idx], safe_metadata))
            
        batch_size = 50
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i + batch_size], namespace="research_chunks")
        return ids

    def add_source_text(self, source_id: str, text: str, metadata: dict[str, Any]) -> None:
        text = text[:4000] # truncate to avoid large metadata
        embedding = self.embedding_service.embed([text])[0]
        safe_metadata = {k: v for k, v in metadata.items() if v is not None}
        safe_metadata["text"] = text
        self.index.upsert(vectors=[(source_id, embedding, safe_metadata)], namespace="research_documents")

    def query(self, query: str, top_k: int = 8, session_id: str | None = None) -> list[dict[str, Any]]:
        embedding = self.embedding_service.embed([query])[0]
        filter_dict = {"session_id": session_id} if session_id else None
        
        result = self.index.query(
            vector=embedding,
            top_k=top_k,
            namespace="research_chunks",
            filter=filter_dict,
            include_metadata=True
        )
        
        rows: list[dict[str, Any]] = []
        for match in result.matches:
            metadata = match.metadata or {}
            text = metadata.pop("text", "")
            rows.append({
                "id": match.id,
                "text": text,
                "metadata": metadata,
                "score": float(match.score)
            })
        return rows

    def add_paper_artifacts(self, paper: dict, chunks: list[str]) -> None:
        document_id = paper.get("document_id", "")
        
        if chunks:
            embeddings = self.embedding_service.embed(chunks)
            ids = [f"paper_chunk:{document_id}:{idx}" for idx in range(len(chunks))]
            vectors = []
            for idx, chunk in enumerate(chunks):
                vectors.append((
                    ids[idx], 
                    embeddings[idx], 
                    {
                        "document_id": document_id,
                        "filename": paper.get("filename", ""),
                        "title": paper.get("title", ""),
                        "artifact_type": "paper_chunk",
                        "chunk_index": idx,
                        "text": chunk
                    }
                ))
            batch_size = 50
            for i in range(0, len(vectors), batch_size):
                self.index.upsert(vectors=vectors[i:i + batch_size], namespace="paper_chunks")

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
        self._upsert_single("paper_metadata", f"paper_metadata:{document_id}", metadata_text, paper, "paper_metadata")
        self._upsert_list("research_findings", document_id, paper.get("key_findings", []), paper, "research_findings")
        self._upsert_list("research_limitations", document_id, paper.get("limitations", []), paper, "research_limitations")
        self._upsert_list("future_work", document_id, paper.get("future_work", []), paper, "future_work")

    def query_paper_collection(self, collection_name: str, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        embedding = self.embedding_service.embed([query])[0]
        result = self.index.query(
            vector=embedding,
            top_k=top_k,
            namespace=collection_name,
            include_metadata=True
        )
        return [
            {
                "id": match.id,
                "text": match.metadata.get("text", "") if match.metadata else "",
                "metadata": {k: v for k, v in (match.metadata or {}).items() if k != "text"},
                "score": float(match.score)
            }
            for match in result.matches
        ]

    def _upsert_list(self, namespace: str, document_id: str, values: list[str], paper: dict, artifact_type: str) -> None:
        clean = [value for value in values if value.strip()]
        if not clean:
            return
        embeddings = self.embedding_service.embed(clean)
        ids = [f"{artifact_type}:{document_id}:{idx}" for idx in range(len(clean))]
        
        vectors = []
        for idx, val in enumerate(clean):
            vectors.append((
                ids[idx], 
                embeddings[idx], 
                {
                    "document_id": document_id,
                    "filename": paper.get("filename", ""),
                    "title": paper.get("title", ""),
                    "artifact_type": artifact_type,
                    "text": val
                }
            ))
        self.index.upsert(vectors=vectors, namespace=namespace)

    def _upsert_single(self, namespace: str, row_id: str, text: str, paper: dict, artifact_type: str) -> None:
        embedding = self.embedding_service.embed([text or paper.get("title", "Untitled paper")])[0]
        self.index.upsert(
            vectors=[(
                row_id,
                embedding,
                {
                    "document_id": paper.get("document_id", ""),
                    "filename": paper.get("filename", ""),
                    "title": paper.get("title", ""),
                    "artifact_type": artifact_type,
                    "text": text
                }
            )],
            namespace=namespace
        )

# Maintain alias for compatibility during migration if necessary
ChromaVectorStore = PineconeVectorStore
