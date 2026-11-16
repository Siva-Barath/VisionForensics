"""
report.py — Database model for Forensic Investigation Reports.
Persists metadata, cryptographic SHA-256 integrity hashes, analysis snapshots,
and disk paths for generated defense-grade PDF reports.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User
    from app.models.comparison import DocumentComparison


class ForensicReport(Base):
    __tablename__ = "forensic_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_number: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    comparison_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("document_comparisons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="GENERATED", nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    analysis_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", foreign_keys=[document_id])
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    comparison: Mapped[Optional["DocumentComparison"]] = relationship("DocumentComparison", foreign_keys=[comparison_id])

    def __repr__(self) -> str:
        return f"<ForensicReport id={self.id} number={self.report_number} doc={self.document_id}>"
