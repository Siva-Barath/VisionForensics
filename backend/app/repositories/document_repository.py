"""
document_repository.py — Data access and persistence repository for documents, pages,
analyses, evidence records, and detected regions.
"""

from __future__ import annotations
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, func, or_

from app.models.document import Document
from app.models.case import Case
from app.models.page import DocumentPage
from app.models.analysis import Analysis
from app.models.evidence import EvidenceRecord
from app.models.region import DetectedRegion
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository handling all database operations for forensic document analysis."""

    def __init__(self, db_session: Session, auto_commit: bool = True) -> None:
        self.db = db_session
        self.auto_commit = auto_commit

    def _finish(self):
        if self.auto_commit:
            self.db.commit()
        else:
            self.db.flush()

    # ------------------------------------------------------------------ #
    # Document Operations                                                #
    # ------------------------------------------------------------------ #

    def save_document(
        self,
        document_id: str,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_type: str,
        size_bytes: int,
        sha256_hash: Optional[str] = None,
        page_count: Optional[int] = 1,
        status: str = "uploaded",
        case_id: Optional[str] = None,
        uploader_id: Optional[str] = None,
    ) -> Document:
        """Create or update a document exhibit record."""
        doc = self.db.get(Document, document_id)
        if doc is None:
            doc = Document(
                id=document_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_type=file_type,
                size_bytes=size_bytes,
                sha256_hash=sha256_hash,
                page_count=page_count,
                status=status,
                case_id=case_id,
                uploader_id=uploader_id,
            )
            self.db.add(doc)
        else:
            doc.original_filename = original_filename
            doc.stored_filename = stored_filename
            doc.file_path = file_path
            doc.file_type = file_type
            doc.size_bytes = size_bytes
            if sha256_hash:
                doc.sha256_hash = sha256_hash
            if page_count:
                doc.page_count = page_count
            doc.status = status
            if case_id:
                doc.case_id = case_id
            if uploader_id:
                doc.uploader_id = uploader_id

        self._finish()
        self.db.refresh(doc)
        return doc

    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by its primary key ID."""
        return self.db.get(Document, document_id)

    def visible_documents_query(self, user=None):
        stmt = select(Document)
        if user is not None and user.role != "SYSTEM_ADMINISTRATOR":
            case_access = Document.case.has() if user.role == "SENIOR_INVESTIGATOR" else Document.case.has(Case.lead_investigator_id == user.id)
            stmt = stmt.where(or_(Document.uploader_id == user.id, case_access))
        return stmt

    def list_documents(self, skip: int = 0, limit: int = 100, user=None) -> List[Document]:
        """Filter visibility before pagination; do not truncate another user's records first."""
        stmt = self.visible_documents_query(user)
        stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    # ------------------------------------------------------------------ #
    # Document Page Operations                                           #
    # ------------------------------------------------------------------ #

    def save_document_pages(
        self,
        document_id: str,
        pages_data: List[Dict[str, Any]],
    ) -> List[DocumentPage]:
        """Persist rasterized pages for a document exhibit."""
        existing_pages = self.get_document_pages(document_id)
        existing_map = {p.page_index: p for p in existing_pages}

        saved_pages = []
        for p_data in pages_data:
            page_idx = p_data.get("page_index", 0)
            if page_idx in existing_map:
                page = existing_map[page_idx]
                page.image_path = p_data.get("image_path", page.image_path)
                page.width = p_data.get("width", page.width)
                page.height = p_data.get("height", page.height)
                page.dpi = p_data.get("dpi", page.dpi)
            else:
                page = DocumentPage(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    page_index=page_idx,
                    image_path=p_data.get("image_path", ""),
                    width=p_data.get("width", 0),
                    height=p_data.get("height", 0),
                    dpi=p_data.get("dpi", 200),
                )
                self.db.add(page)
            saved_pages.append(page)

        self._finish()
        return saved_pages

    def get_document_pages(self, document_id: str) -> List[DocumentPage]:
        """Retrieve all pages for a document exhibit ordered by page index."""
        stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_index.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_document_page(self, document_id: str, page_index: int = 0) -> Optional[DocumentPage]:
        """Retrieve a specific page for a document exhibit."""
        stmt = select(DocumentPage).where(
            DocumentPage.document_id == document_id,
            DocumentPage.page_index == page_index,
        )
        return self.db.scalars(stmt).first()

    # ------------------------------------------------------------------ #
    # Analysis Operations (with Historical Versioning)                   #
    # ------------------------------------------------------------------ #

    def save_analysis(
        self,
        document_id: str,
        job_id: str,
        unified_risk_tier: str,
        overall_verdict: str,
        risk_description: Optional[str],
        composite_risk_score: float,
        ml_available: bool,
        ml_status: str,
        ml_forgery_probability: Optional[float],
        ml_predicted_class: Optional[str],
        ml_operational_threshold: float,
        ml_feature_completeness: float,
        ml_top_features: Dict[str, Any],
        ml_imputed_features: Dict[str, Any],
        symbolic_available: bool,
        symbolic_severity_score: float,
        symbolic_evidence: List[Dict[str, Any]],
        decision_trace: List[Dict[str, Any]],
        limitations: List[Dict[str, Any]],
        warnings: List[str],
        processing_time_ms: Optional[float],
        evidence_list: Optional[List[Dict[str, Any]]] = None,
        detected_regions: Optional[List[Dict[str, Any]]] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Analysis:
        """
        Persists a forensic analysis result with automatic version incrementing.
        Marks all existing analyses for this document as is_latest=False.
        """
        # 1. Determine next version number
        max_ver_stmt = select(func.max(Analysis.version)).where(Analysis.document_id == document_id)
        current_max = self.db.scalar(max_ver_stmt) or 0
        next_version = current_max + 1

        # 2. Demote prior versions
        if current_max > 0:
            demote_stmt = (
                update(Analysis)
                .where(Analysis.document_id == document_id, Analysis.is_latest.is_(True))
                .values(is_latest=False)
            )
            self.db.execute(demote_stmt)

        # 3. Create new Analysis record
        analysis_id = str(uuid.uuid4())
        analysis = Analysis(
            id=analysis_id,
            document_id=document_id,
            job_id=job_id,
            version=next_version,
            is_latest=True,
            unified_risk_tier=unified_risk_tier,
            overall_verdict=overall_verdict,
            risk_description=risk_description,
            composite_risk_score=composite_risk_score,
            ml_available=ml_available,
            ml_status=ml_status,
            ml_forgery_probability=ml_forgery_probability,
            ml_predicted_class=ml_predicted_class,
            ml_operational_threshold=ml_operational_threshold,
            ml_feature_completeness=ml_feature_completeness,
            ml_top_features=ml_top_features or {},
            ml_imputed_features=ml_imputed_features or {},
            symbolic_available=symbolic_available,
            symbolic_severity_score=symbolic_severity_score,
            symbolic_evidence=symbolic_evidence or [],
            decision_trace=decision_trace or [],
            limitations=limitations or [],
            warnings=warnings or [],
            processing_time_ms=processing_time_ms,
            context_snapshot=context_snapshot,
        )
        self.db.add(analysis)

        # 4. Create Evidence Records
        evidence_map: Dict[str, str] = {}
        for ev in evidence_list or []:
            ev_id = str(ev.get("id") or uuid.uuid4())
            evidence_rec = EvidenceRecord(
                id=ev_id,
                analysis_id=analysis_id,
                detector=str(ev.get("detector", "unknown")),
                category=str(ev.get("category", "UNKNOWN")),
                severity=float(ev.get("severity", 0.0)),
                confidence=float(ev.get("confidence", 1.0)),
                reliability=float(ev.get("reliability", 1.0)),
                description=str(ev.get("description", "")),
                recommendation=ev.get("recommendation"),
            )
            self.db.add(evidence_rec)
            evidence_map[ev_id] = ev_id

        # 5. Create Detected Regions
        for idx, reg in enumerate(detected_regions or []):
            reg_id = str(reg.get("id") or f"reg_{analysis_id[:8]}_{idx}")
            ev_id = reg.get("evidence_id")
            if ev_id and ev_id not in evidence_map:
                ev_id = None

            detected_reg = DetectedRegion(
                id=reg_id,
                analysis_id=analysis_id,
                evidence_id=ev_id,
                document_id=document_id,
                page_index=int(reg.get("page_index", 0)),
                detector=str(reg.get("detector", "unknown")),
                category=str(reg.get("category", "UNKNOWN")),
                severity=float(reg.get("severity", 0.0)),
                confidence=float(reg.get("confidence", 1.0)),
                description=str(reg.get("description", "")),
                points_json=reg.get("bounding_box", {}).get("points") or reg.get("points_json", []),
            )
            self.db.add(detected_reg)

        self._finish()
        self.db.refresh(analysis)
        logger.info(
            "Persisted analysis | doc=%s v=%d tier=%s regions=%d",
            document_id,
            next_version,
            unified_risk_tier,
            len(detected_regions or []),
        )
        return analysis

    def get_latest_analysis(self, document_id: str) -> Optional[Analysis]:
        """
        Retrieve the latest version analysis for a document exhibit,
        eagerly loading evidence records and detected regions.
        """
        stmt = (
            select(Analysis)
            .where(Analysis.document_id == document_id, Analysis.is_latest.is_(True))
            .options(
                joinedload(Analysis.evidence_records),
                joinedload(Analysis.detected_regions),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_analysis_by_version(self, document_id: str, version: int) -> Optional[Analysis]:
        """Retrieve a specific historical version of an analysis."""
        stmt = (
            select(Analysis)
            .where(Analysis.document_id == document_id, Analysis.version == version)
            .options(
                joinedload(Analysis.evidence_records),
                joinedload(Analysis.detected_regions),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def list_analyses_for_document(self, document_id: str) -> List[Analysis]:
        """List all historical versions of analyses for a document."""
        stmt = (
            select(Analysis)
            .where(Analysis.document_id == document_id)
            .order_by(Analysis.version.desc())
        )
        return list(self.db.scalars(stmt).all())
