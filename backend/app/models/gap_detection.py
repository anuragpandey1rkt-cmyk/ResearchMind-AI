from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from app.models.research import uuid_str


class ResearchGapAnalysis(Base):
    __tablename__ = "research_gap_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    research_domain: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    document_ids: Mapped[list] = mapped_column(JSON, default=list)
    paper_summaries: Mapped[list] = mapped_column(JSON, default=list)
    theme_clusters: Mapped[list] = mapped_column(JSON, default=list)
    contradictions: Mapped[list] = mapped_column(JSON, default=list)
    gaps: Mapped[list] = mapped_column(JSON, default=list)
    innovations: Mapped[list] = mapped_column(JSON, default=list)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    knowledge_graph: Mapped[dict] = mapped_column(JSON, default=dict)
    visualizations: Mapped[dict] = mapped_column(JSON, default=dict)
    report_markdown: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
