from fastapi import HTTPException
from app.agents.gap_workflow import GapDetectionWorkflow
from app.repositories.research_repository import ResearchRepository
from app.schemas.gap_detection import GapDetectionResponse


class GapDetectionService:
    def __init__(self, repo: ResearchRepository) -> None:
        self.repo = repo
        self.workflow = GapDetectionWorkflow()

    async def run(self, document_ids: list[str], research_domain: str, top_k: int = 12) -> GapDetectionResponse:
        documents = await self.repo.get_documents(document_ids)
        found_ids = {document.id for document in documents}
        missing = [document_id for document_id in document_ids if document_id not in found_ids]
        if missing:
            raise HTTPException(status_code=404, detail=f"Documents not found: {', '.join(missing)}")
        if len(documents) < 2:
            raise HTTPException(status_code=400, detail="Upload at least two papers for gap detection.")

        analysis = await self.repo.create_gap_analysis(research_domain, document_ids)
        state = await self.workflow.run(analysis.id, documents, research_domain, top_k)
        analysis = await self.repo.update_gap_analysis(
            analysis,
            status="completed",
            paper_summaries=state.get("papers", []),
            theme_clusters=state.get("theme_clusters", []),
            contradictions=state.get("contradictions", []),
            gaps=state.get("gaps", []),
            innovations=state.get("innovations", []),
            scores=state.get("scores", {}),
            knowledge_graph=state.get("knowledge_graph", {}),
            visualizations=state.get("visualizations", {}),
            report_markdown=state.get("report_markdown", ""),
        )
        return self._to_response(analysis)

    def _to_response(self, analysis) -> GapDetectionResponse:
        return GapDetectionResponse(
            analysis_id=analysis.id,
            status=analysis.status,
            research_domain=analysis.research_domain,
            papers=analysis.paper_summaries,
            theme_clusters=analysis.theme_clusters,
            contradictions=analysis.contradictions,
            gaps=analysis.gaps,
            innovations=analysis.innovations,
            scores=analysis.scores,
            knowledge_graph=analysis.knowledge_graph,
            visualizations=analysis.visualizations,
            report_markdown=analysis.report_markdown,
            created_at=analysis.created_at,
        )
