"""
report_repository.py — Data access repository for Forensic Investigation Reports.
Persists and retrieves defense-grade PDF report records with cryptographic hash tracking.
"""

from __future__ import annotations
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.report import ForensicReport
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReportRepository:
    """Repository handling all database persistence for forensic PDF reports."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def create_report(
        self,
        report_number: str,
        document_id: str,
        title: str,
        file_path: str,
        sha256_hash: str,
        file_size_bytes: int,
        page_count: int,
        analysis_version: int = 1,
        user_id: Optional[str] = None,
        comparison_id: Optional[str] = None,
        analyst_notes: Optional[str] = None,
        metadata_snapshot: Optional[Dict[str, Any]] = None,
        report_id: Optional[str] = None,
    ) -> ForensicReport:
        """Creates and commits a new forensic report entity."""
        rep = ForensicReport(
            id=report_id or str(uuid.uuid4()),
            report_number=report_number,
            document_id=document_id,
            user_id=user_id,
            comparison_id=comparison_id,
            title=title,
            status="GENERATED",
            file_path=file_path,
            sha256_hash=sha256_hash,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            analysis_version=analysis_version,
            analyst_notes=analyst_notes,
            metadata_snapshot=metadata_snapshot or {},
        )
        self.db.add(rep)
        self.db.commit()
        self.db.refresh(rep)
        logger.info(
            "Created ForensicReport %s (%s) for document %s",
            rep.id,
            rep.report_number,
            document_id,
        )
        return rep

    def get_report(self, report_id: str) -> Optional[ForensicReport]:
        """Retrieves a report by its primary UUID key with document and user relationships."""
        stmt = (
            select(ForensicReport)
            .options(
                joinedload(ForensicReport.document),
                joinedload(ForensicReport.user),
                joinedload(ForensicReport.comparison),
            )
            .where(ForensicReport.id == report_id)
        )
        return self.db.scalars(stmt).first()

    def get_reports_for_document(self, document_id: str) -> List[ForensicReport]:
        """Returns all reports generated for a particular document exhibit."""
        stmt = (
            select(ForensicReport)
            .where(ForensicReport.document_id == document_id)
            .order_by(ForensicReport.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_reports(self, limit: int = 50, offset: int = 0) -> List[ForensicReport]:
        """Lists recent forensic reports with pagination."""
        stmt = (
            select(ForensicReport)
            .options(joinedload(ForensicReport.document), joinedload(ForensicReport.user))
            .order_by(ForensicReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
