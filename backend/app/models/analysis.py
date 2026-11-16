"""
Analysis ORM model.
Stores forensic evaluation results with strict versioning.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.evidence import EvidenceRecord
    from app.models.region import DetectedRegion


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_analyses_doc_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Synthesis Verdicts
    unified_risk_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    overall_verdict: Mapped[str] = mapped_column(String(100), nullable=False, default="INCONCLUSIVE")
    risk_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    composite_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Track 1 ML Statistics
    ml_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ml_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNAVAILABLE")
    ml_forgery_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_predicted_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ml_operational_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.40)
    ml_feature_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    ml_top_features: Mapped[dict] = mapped_column(JSON, default=dict)
    ml_imputed_features: Mapped[dict] = mapped_column(JSON, default=dict)

    # Track 2 Symbolic Metrics
    symbolic_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    symbolic_severity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    symbolic_evidence: Mapped[list] = mapped_column(JSON, default=list)

    # Traceability & Explanations
    decision_trace: Mapped[list] = mapped_column(JSON, default=list)
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Nullable for historical analyses. Never invent or backfill missing evidence.
    context_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="analyses")
    evidence_records: Mapped[List["EvidenceRecord"]] = relationship(
        "EvidenceRecord", back_populates="analysis", cascade="all, delete-orphan"
    )
    detected_regions: Mapped[List["DetectedRegion"]] = relationship(
        "DetectedRegion", back_populates="analysis", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Analysis id={self.id} doc={self.document_id} v={self.version} tier={self.unified_risk_tier}>"
