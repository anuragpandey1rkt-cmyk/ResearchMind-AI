from typing import TypedDict


class GapDetectionState(TypedDict, total=False):
    analysis_id: str
    research_domain: str
    top_k: int
    documents: list[dict]
    papers: list[dict]
    theme_clusters: list[dict]
    contradictions: list[dict]
    gaps: list[dict]
    innovations: list[dict]
    scores: dict
    knowledge_graph: dict
    retrieval_context: dict
    visualizations: dict
    report_markdown: str
