from app.services.vector_store import ChromaVectorStore


class RetrievalService:
    def __init__(self, vector_store: ChromaVectorStore | None = None) -> None:
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, query: str, top_k: int = 8, session_id: str | None = None) -> list[dict]:
        rows = self.vector_store.query(query=query, top_k=top_k, session_id=session_id)
        if not rows and session_id:
            rows = self.vector_store.query(query=query, top_k=top_k, session_id=None)
        query_terms = {term.lower() for term in query.split() if len(term) > 3}
        for row in rows:
            text = row["text"].lower()
            overlap = sum(1 for term in query_terms if term in text)
            row["rerank_score"] = round(float(row["score"]) + overlap * 0.03, 4)
        return sorted(rows, key=lambda item: item["rerank_score"], reverse=True)
