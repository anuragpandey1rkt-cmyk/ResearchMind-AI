from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class ResearchRequest(BaseModel):
    query: str = Field(min_length=8, max_length=4000)
    session_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=20)
    stream: bool = False


class ResearchPlanTask(BaseModel):
    title: str
    objective: str
    search_queries: list[str]


class ResearchPlan(BaseModel):
    objective: str
    subtopics: list[str]
    tasks: list[ResearchPlanTask]


class Source(BaseModel):
    title: str
    url: str
    snippet: str
    rank: int = 0


class CitationOut(BaseModel):
    id: str | None = None
    title: str
    url: str | None = None
    authors: str | None = None
    source_type: str = "web"
    snippet: str | None = None
    confidence: int = 80


class ResearchReportOut(BaseModel):
    id: str | None = None
    session_id: str
    title: str
    markdown: str
    citations: list[CitationOut] = []
    created_at: datetime | None = None


class ResearchResponse(BaseModel):
    session_id: str
    status: str
    plan: ResearchPlan | None = None
    sources: list[Source] = []
    context: list[dict] = []
    report: ResearchReportOut | None = None


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_count: int
    extracted_chars: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=8, ge=1, le=20)
