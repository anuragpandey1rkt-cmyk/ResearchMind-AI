from app.agents.workflow import ResearchWorkflow
from app.repositories.research_repository import ResearchRepository
from app.schemas.research import CitationOut, ResearchReportOut, ResearchResponse
from app.utils.security import sanitize_research_query


class ResearchService:
    def __init__(self, repo: ResearchRepository) -> None:
        self.repo = repo
        self.workflow = ResearchWorkflow()

    async def run_research(self, query: str, session_id: str | None = None, top_k: int = 8) -> ResearchResponse:
        clean_query = sanitize_research_query(query)
        session = await self.repo.get_session(session_id) if session_id else None
        if session is None:
            session = await self.repo.create_session(clean_query)
        else:
            session = await self.repo.update_session(session, query=clean_query, status="running")

        await self.repo.add_history(session.id, "research_started", {"query": clean_query})
        state = await self.workflow.run(session_id=session.id, query=clean_query, top_k=top_k)
        citations = await self.repo.add_citations(state.get("citations", [])) if state.get("citations") else []
        report = await self.repo.add_report(
            session_id=session.id,
            title=state.get("title", "Research Report"),
            markdown=state.get("report_markdown", ""),
            metadata={"source_count": len(state.get("sources", [])), "context_count": len(state.get("context", []))},
        )
        session = await self.repo.update_session(
            session,
            status="completed",
            plan=state.get("plan"),
            sources=state.get("sources", []),
        )
        await self.repo.add_history(session.id, "research_completed", {"report_id": report.id})

        citation_out = [
            CitationOut(
                id=row.id,
                title=row.title,
                url=row.url,
                authors=row.authors,
                source_type=row.source_type,
                snippet=row.snippet,
                confidence=row.confidence,
            )
            for row in citations
        ]
        return ResearchResponse(
            session_id=session.id,
            status=session.status,
            plan=session.plan,
            sources=session.sources or [],
            context=state.get("context", []),
            report=ResearchReportOut(
                id=report.id,
                session_id=session.id,
                title=report.title,
                markdown=report.markdown,
                citations=citation_out,
                created_at=report.created_at,
            ),
        )
