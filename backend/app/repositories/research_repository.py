from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.gap_detection import ResearchGapAnalysis
from app.models.research import Citation, ResearchHistory, ResearchReport, ResearchSession, UploadedDocument


class ResearchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, query: str, user_id: str | None = None) -> ResearchSession:
        session = ResearchSession(query=query, user_id=user_id, status="running")
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> ResearchSession | None:
        return await self.db.get(ResearchSession, session_id)

    async def update_session(self, session: ResearchSession, **values) -> ResearchSession:
        for key, value in values.items():
            setattr(session, key, value)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def list_sessions(self, limit: int = 50) -> list[ResearchSession]:
        result = await self.db.execute(
            select(ResearchSession).order_by(desc(ResearchSession.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def add_report(self, session_id: str, title: str, markdown: str, metadata: dict | None = None) -> ResearchReport:
        report = ResearchReport(session_id=session_id, title=title, markdown=markdown, metadata_json=metadata)
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_report(self, report_id: str) -> ResearchReport | None:
        return await self.db.get(ResearchReport, report_id)

    async def latest_report_for_session(self, session_id: str) -> ResearchReport | None:
        result = await self.db.execute(
            select(ResearchReport)
            .where(ResearchReport.session_id == session_id)
            .order_by(desc(ResearchReport.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def add_citations(self, citations: list[dict]) -> list[Citation]:
        rows = [Citation(**citation) for citation in citations]
        self.db.add_all(rows)
        await self.db.commit()
        for row in rows:
            await self.db.refresh(row)
        return rows

    async def citations_for_session(self, session_id: str) -> list[Citation]:
        result = await self.db.execute(select(Citation).where(Citation.session_id == session_id))
        return list(result.scalars().all())

    async def add_document(self, **values) -> UploadedDocument:
        document = UploadedDocument(**values)
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_document(self, document_id: str) -> UploadedDocument | None:
        return await self.db.get(UploadedDocument, document_id)

    async def get_documents(self, document_ids: list[str]) -> list[UploadedDocument]:
        result = await self.db.execute(select(UploadedDocument).where(UploadedDocument.id.in_(document_ids)))
        return list(result.scalars().all())

    async def add_history(self, session_id: str, event_type: str, payload: dict) -> ResearchHistory:
        event = ResearchHistory(session_id=session_id, event_type=event_type, payload=payload)
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def create_gap_analysis(
        self,
        research_domain: str,
        document_ids: list[str],
        user_id: str | None = None,
    ) -> ResearchGapAnalysis:
        analysis = ResearchGapAnalysis(
            user_id=user_id,
            research_domain=research_domain,
            document_ids=document_ids,
            status="running",
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis

    async def get_gap_analysis(self, analysis_id: str) -> ResearchGapAnalysis | None:
        return await self.db.get(ResearchGapAnalysis, analysis_id)

    async def update_gap_analysis(self, analysis: ResearchGapAnalysis, **values) -> ResearchGapAnalysis:
        for key, value in values.items():
            setattr(analysis, key, value)
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis

    async def list_gap_analyses(self, limit: int = 50) -> list[ResearchGapAnalysis]:
        result = await self.db.execute(
            select(ResearchGapAnalysis).order_by(desc(ResearchGapAnalysis.created_at)).limit(limit)
        )
        return list(result.scalars().all())
