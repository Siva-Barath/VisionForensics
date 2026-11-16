"""
DetectedRegion ORM model.
Stores spatial polygon coordinates and detector metadata for visual overlays.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.evidence import EvidenceRecord
    from app.models.document import Document


class DetectedRegion(Base):
    __tablename__ = "detected_regions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    points_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="detected_regions")
    evidence: Mapped[Optional["EvidenceRecord"]] = relationship("EvidenceRecord", back_populates="regions")
    document: Mapped["Document"] = relationship("Document", foreign_keys=[document_id])

    def __repr__(self) -> str:
        return f"<DetectedRegion id={self.id} detector={self.detector} severity={self.severity}>"
