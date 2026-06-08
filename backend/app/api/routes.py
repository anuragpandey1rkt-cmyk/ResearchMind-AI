from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from app.api.deps import get_research_repo
from app.repositories.research_repository import ResearchRepository
from app.schemas.gap_detection import GapDetectionRequest, GapDetectionResponse, GapUploadResponse
from app.schemas.research import ResearchRequest, ResearchResponse, SearchRequest, UploadResponse
from app.services.document_service import DocumentService
from app.services.export_service import ExportService
from app.services.gap_detection_service import GapDetectionService
from app.services.groq_client import GroqClient
from app.services.research_service import ResearchService
from app.services.search_service import SearchService
from app.utils.rate_limit import rate_limiter
from app.utils.security import sanitize_research_query, validate_pdf_upload


router = APIRouter(dependencies=[Depends(rate_limiter)])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ResearchMind"}


@router.post("/research", response_model=ResearchResponse)
async def research(payload: ResearchRequest, repo: ResearchRepository = Depends(get_research_repo)):
    service = ResearchService(repo)
    return await service.run_research(payload.query, payload.session_id, payload.top_k)


@router.post("/research/stream")
async def research_stream(payload: ResearchRequest):
    clean_query = sanitize_research_query(payload.query)
    groq = GroqClient()

    async def event_stream():
        messages = [
            {"role": "system", "content": "You are ResearchMind. Produce a concise streaming research answer with citations only when evidence is provided."},
            {"role": "user", "content": clean_query},
        ]
        async for token in groq.stream_chat(messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str | None = None,
    repo: ResearchRepository = Depends(get_research_repo),
):
    data = await validate_pdf_upload(file)
    service = DocumentService(repo)
    document = await service.ingest_pdf(data, file.filename or "document.pdf", file.content_type or "application/pdf", session_id)
    return UploadResponse(
        document_id=document.id,
        filename=document.filename,
        chunks_count=document.chunks_count,
        extracted_chars=document.extracted_chars,
    )


@router.post("/gap-detector/upload", response_model=GapUploadResponse)
async def upload_gap_papers(
    files: list[UploadFile] = File(...),
    repo: ResearchRepository = Depends(get_research_repo),
):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one PDF paper.")
    service = DocumentService(repo)
    documents = []
    for file in files:
        data = await validate_pdf_upload(file)
        document = await service.ingest_pdf(
            data,
            file.filename or "paper.pdf",
            file.content_type or "application/pdf",
            session_id=None,
        )
        documents.append(
            {
                "document_id": document.id,
                "filename": document.filename,
                "chunks_count": document.chunks_count,
                "extracted_chars": document.extracted_chars,
            }
        )
    return GapUploadResponse(documents=documents)


@router.post("/gap-detector/analyze", response_model=GapDetectionResponse)
async def analyze_research_gaps(
    payload: GapDetectionRequest,
    repo: ResearchRepository = Depends(get_research_repo),
):
    service = GapDetectionService(repo)
    return await service.run(payload.document_ids, payload.research_domain, payload.top_k)


@router.get("/gap-detector/history")
async def gap_history(repo: ResearchRepository = Depends(get_research_repo)):
    analyses = await repo.list_gap_analyses()
    return [
        {
            "id": analysis.id,
            "research_domain": analysis.research_domain,
            "status": analysis.status,
            "paper_count": len(analysis.document_ids or []),
            "gap_count": len(analysis.gaps or []),
            "created_at": analysis.created_at,
        }
        for analysis in analyses
    ]


@router.get("/gap-detector/{analysis_id}", response_model=GapDetectionResponse)
async def get_gap_analysis(analysis_id: str, repo: ResearchRepository = Depends(get_research_repo)):
    analysis = await repo.get_gap_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found.")
    return GapDetectionService(repo)._to_response(analysis)


@router.get("/gap-detector/{analysis_id}/pdf")
async def gap_analysis_pdf(analysis_id: str, repo: ResearchRepository = Depends(get_research_repo)):
    analysis = await repo.get_gap_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found.")
    pdf = ExportService().markdown_to_pdf(analysis.report_markdown, f"{analysis.research_domain} Research Gap Report")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{analysis.research_domain[:70]}-gap-report.pdf"'},
    )


@router.get("/history")
async def history(repo: ResearchRepository = Depends(get_research_repo)):
    sessions = await repo.list_sessions()
    return [
        {
            "id": session.id,
            "query": session.query,
            "status": session.status,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "source_count": len(session.sources or []),
        }
        for session in sessions
    ]


@router.get("/report/{report_id}")
async def report(report_id: str, repo: ResearchRepository = Depends(get_research_repo)):
    row = await repo.get_report(report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    citations = await repo.citations_for_session(row.session_id)
    return {
        "id": row.id,
        "session_id": row.session_id,
        "title": row.title,
        "markdown": row.markdown,
        "citations": [
            {
                "id": citation.id,
                "title": citation.title,
                "url": citation.url,
                "source_type": citation.source_type,
                "snippet": citation.snippet,
                "confidence": citation.confidence,
            }
            for citation in citations
        ],
        "created_at": row.created_at,
    }


@router.get("/report/{report_id}/pdf")
async def report_pdf(report_id: str, repo: ResearchRepository = Depends(get_research_repo)):
    row = await repo.get_report(report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    pdf = ExportService().markdown_to_pdf(row.markdown, row.title)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{row.title[:80]}.pdf"'},
    )


@router.get("/citations/{session_id}")
async def citations(session_id: str, repo: ResearchRepository = Depends(get_research_repo)):
    rows = await repo.citations_for_session(session_id)
    return [
        {
            "id": row.id,
            "title": row.title,
            "url": row.url,
            "authors": row.authors,
            "source_type": row.source_type,
            "snippet": row.snippet,
            "confidence": row.confidence,
        }
        for row in rows
    ]


@router.post("/search")
async def search(payload: SearchRequest):
    service = SearchService()
    return [source.model_dump() for source in await service.search(payload.query, payload.max_results)]
