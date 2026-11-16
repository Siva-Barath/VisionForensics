"""
comparison.py — Database model for Document Comparison exhibits and results.
Persists structural, visual, and metadata comparisons between two document exhibits.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User


class DocumentComparison(Base):
    __tablename__ = "document_comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ssim_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    difference_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alignment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNALIGNED")
    alignment_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    verdict_category: Mapped[str] = mapped_column(String(50), nullable=False, default="LOCALIZED_DIFFERENCES")

    differential_regions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    metadata_diff: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    artifacts: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    document_a: Mapped["Document"] = relationship("Document", foreign_keys=[document_a_id])
    document_b: Mapped["Document"] = relationship("Document", foreign_keys=[document_b_id])
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"<DocumentComparison id={self.id} doc_a={self.document_a_id} "
            f"doc_b={self.document_b_id} similarity={self.similarity_score}>"
        )
