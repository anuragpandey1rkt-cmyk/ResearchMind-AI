from datetime import datetime
from pydantic import BaseModel, Field


class PaperSection(BaseModel):
    title: str
    abstract: str = ""
    methodology: str = ""
    results: str = ""
    limitations: str = ""
    future_work: str = ""


class PaperSummary(BaseModel):
    document_id: str
    filename: str
    title: str
    authors: list[str] = []
    abstract: str = ""
    methodology: str = ""
    results: str = ""
    limitations: list[str] = []
    future_work: list[str] = []
    key_findings: list[str] = []
    methods: list[str] = []
    datasets: list[str] = []
    metrics: list[str] = []
    research_areas: list[str] = []


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    score: float = 1.0


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    weight: float = 1.0


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []


class ThemeCluster(BaseModel):
    name: str
    papers: list[str] = []
    concepts: list[str] = []
    saturation_score: int = Field(default=50, ge=0, le=100)


class Contradiction(BaseModel):
    claim_a: str
    claim_b: str
    papers: list[str]
    severity: int = Field(default=50, ge=0, le=100)
    explanation: str


class GapItem(BaseModel):
    category: str
    description: str
    evidence: list[str] = []
    novelty_score: int = Field(default=50, ge=0, le=100)
    impact_score: int = Field(default=50, ge=0, le=100)
    feasibility_score: int = Field(default=50, ge=0, le=100)


class InnovationSuggestion(BaseModel):
    title: str
    type: str
    rationale: str
    novelty_score: int = Field(default=50, ge=0, le=100)
    feasibility_score: int = Field(default=50, ge=0, le=100)
    impact_score: int = Field(default=50, ge=0, le=100)
    commercialization_potential_score: int = Field(default=50, ge=0, le=100)


class GapScores(BaseModel):
    novelty_score: int = Field(ge=0, le=100)
    research_saturation_score: int = Field(ge=0, le=100)
    impact_score: int = Field(ge=0, le=100)
    feasibility_score: int = Field(ge=0, le=100)
    commercialization_potential_score: int = Field(ge=0, le=100)


class GapDetectionRequest(BaseModel):
    document_ids: list[str] = Field(min_length=2, max_length=25)
    research_domain: str = Field(default="General research", min_length=3, max_length=300)
    top_k: int = Field(default=12, ge=3, le=30)


class GapDetectionResponse(BaseModel):
    analysis_id: str
    status: str
    research_domain: str
    papers: list[PaperSummary]
    theme_clusters: list[ThemeCluster]
    contradictions: list[Contradiction]
    gaps: list[GapItem]
    innovations: list[InnovationSuggestion]
    scores: GapScores
    knowledge_graph: KnowledgeGraph
    visualizations: dict
    report_markdown: str
    created_at: datetime | None = None


class GapUploadResponse(BaseModel):
    documents: list[dict]
