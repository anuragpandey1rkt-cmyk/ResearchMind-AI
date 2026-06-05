from typing import TypedDict
from app.schemas.research import ResearchPlan, Source


class ResearchState(TypedDict, total=False):
    session_id: str
    query: str
    top_k: int
    plan: dict
    sources: list[dict]
    context: list[dict]
    citations: list[dict]
    report_markdown: str
    title: str
