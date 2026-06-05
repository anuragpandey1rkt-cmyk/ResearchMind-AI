from app.services.vector_store import ChromaVectorStore


class GapRetrievalService:
    def __init__(self, vector_store: ChromaVectorStore | None = None) -> None:
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve_for_gap_detection(self, domain: str, top_k: int = 12) -> dict[str, list[dict]]:
        queries = {
            "paper_chunks": f"{domain} methods datasets metrics limitations future work",
            "paper_metadata": f"{domain} paper metadata authors methods datasets metrics research areas",
            "research_findings": f"{domain} key findings conclusions evidence",
            "research_limitations": f"{domain} limitations threats validity missing experiments",
            "future_work": f"{domain} future work open problems research directions",
        }
        return {
            collection: self.vector_store.query_paper_collection(collection, query, top_k=top_k)
            for collection, query in queries.items()
        }
