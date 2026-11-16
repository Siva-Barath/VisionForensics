"""
report_service.py — Forensic Investigation Report Generation & Export Service.

Orchestrates:
1. Compilation of defense-grade PDF reports consolidating analysis, multi-page findings,
   symbolic evidence, document comparisons, and chain of custody.
2. Cryptographic SHA-256 hash tracking and verification for every generated report.
3. Isolated filesystem persistence under reports_dir.
4. Chain-of-custody audit logging for REPORT_GENERATED and REPORT_DOWNLOADED events.
"""

from __future__ import annotations
import os
import uuid
import hashlib
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pypdf import PdfReader

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.document import Document
from app.models.analysis import Analysis
from app.models.report import ForensicReport
from app.models.audit import ExhibitCustodyLog
from app.repositories.report_repository import ReportRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.comparison_repository import ComparisonRepository
from app.services.audit_service import AuditService
from app.core.security import verify_file_integrity
from app.core.exhibit_integrity import require_exhibit_integrity
from app.services.report_generation.pdf_generator import ForensicPDFBuilder
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReportService:
    """Service managing forensic report generation, persistence, and verified export."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.builder = ForensicPDFBuilder()

    def generate_report(
        self,
        db: Session,
        document: Document,
        user_id: Optional[str] = None,
        comparison_id: Optional[str] = None,
        title: Optional[str] = None,
        analyst_notes: Optional[str] = None,
        user_name: str = "Forensic Analyst",
        user_role: str = "FORENSIC_ANALYST",
        ip_address: Optional[str] = None,
    ) -> ForensicReport:
        """
        Compiles, hashes, persists, and audits a forensic investigation PDF report.
        """
        client_ip = ip_address or "127.0.0.1"
        require_exhibit_integrity(document, db, user_id, client_ip)
        report_id = str(uuid.uuid4())
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        report_number = f"VF-REP-{date_str}-{report_id[:8].upper()}"

        # 1. Retrieve Analysis Context
        from app import document_service
        context = document_service.get_context(document.id)

        # Assemble analysis data dictionary
        if context:
            ml_pred = context.ml_prediction or {}
            risk_assessment = context.risk_assessment or {}
            t2 = risk_assessment.get("track_2_symbolic", {})
            raw_regions = context.detected_regions or []

            # Safely extract image dimensions from quality metrics
            first_w, first_h = 800, 1000
            if context.quality_metrics and len(context.quality_metrics) > 0:
                qm0 = context.quality_metrics[0]
                first_w = getattr(qm0, "width", 800) if not isinstance(qm0, dict) else qm0.get("width", 800)
                first_h = getattr(qm0, "height", 1000) if not isinstance(qm0, dict) else qm0.get("height", 1000)

            analysis_data = {
                "unified_risk_tier": risk_assessment.get("unified_risk_tier", "UNKNOWN"),
                "overall_verdict": risk_assessment.get("overall_verdict", "INCONCLUSIVE"),
                "risk_description": risk_assessment.get("risk_description", ""),
                "composite_risk_score": context.risk_score if context.risk_score is not None else 0.0,
                "analysis_version": getattr(context, "analysis_version", 1),
                "track_1_ml": {
                    "status": ml_pred.get("status", "UNAVAILABLE"),
                    "forgery_probability": ml_pred.get("forgery_probability"),
                    "predicted_class": ml_pred.get("predicted_class"),
                    "operational_threshold": ml_pred.get("operational_threshold", 0.40),
                    "feature_completeness": ml_pred.get("feature_completeness", 1.0),
                    "top_contributing_features": ml_pred.get("top_contributing_features", {}),
                },
                "track_2_symbolic": {
                    "symbolic_severity_score": t2.get("symbolic_severity_score", 0.0),
                    "symbolic_evidence": t2.get("symbolic_evidence", []),
                },
                "detected_regions": raw_regions,
                "image_dimensions": {
                    "width": first_w,
                    "height": first_h,
                    "page_count": document.page_count or 1,
                },
                "decision_trace": risk_assessment.get("decision_trace", []),
            }
        else:
            # Fallback to database Analysis record if memory context was purged
            doc_repo = DocumentRepository(db)
            db_analysis = doc_repo.get_latest_analysis(document.id)
            if not db_analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No forensic analysis found for document exhibit '{document.id}'.",
                )
            analysis_data = {
                "unified_risk_tier": db_analysis.unified_risk_tier,
                "overall_verdict": db_analysis.overall_verdict,
                "risk_description": db_analysis.risk_description,
                "composite_risk_score": db_analysis.composite_risk_score,
                "analysis_version": db_analysis.version,
                "track_1_ml": {
                    "status": db_analysis.ml_status,
                    "forgery_probability": db_analysis.ml_forgery_probability,
                    "predicted_class": db_analysis.ml_predicted_class,
                    "operational_threshold": db_analysis.ml_operational_threshold,
                    "feature_completeness": db_analysis.ml_feature_completeness,
                    "top_contributing_features": db_analysis.ml_top_features or {},
                },
                "track_2_symbolic": {
                    "symbolic_severity_score": db_analysis.symbolic_severity_score,
                    "symbolic_evidence": db_analysis.symbolic_evidence or [],
                },
                "detected_regions": [
                    {
                        "id": r.id,
                        "page_index": r.page_index,
                        "detector": r.detector,
                        "category": r.category,
                        "severity": r.severity,
                        "bounding_box": {"points": r.points_json or []},
                    }
                    for r in db_analysis.detected_regions
                ],
                "image_dimensions": {"width": 800, "height": 1000, "page_count": document.page_count or 1},
                "decision_trace": db_analysis.decision_trace or [],
            }

        # Raw model output is retained independently of historical document
        # qualification rules; existing unified decisions remain unchanged.
        analysis_data['raw_ml'] = context.raw_ml_prediction if context else None

        # 2. Retrieve Linked Document Comparison (if requested)
        comp_data = None
        if comparison_id:
            comp_repo = ComparisonRepository(db)
            comp = comp_repo.get_comparison(comparison_id)
            if comp and (comp.document_a_id == document.id or comp.document_b_id == document.id):
                comp_data = {
                    "comparison_id": comp.id,
                    "document_a_id": comp.document_a_id,
                    "document_b_id": comp.document_b_id,
                    "page_a": comp.page_a,
                    "page_b": comp.page_b,
                    "alignment": {
                        "status": comp.alignment_status,
                        "confidence": comp.alignment_confidence,
                    },
                    "metrics": {
                        "similarity_score": comp.similarity_score,
                        "ssim_score": comp.ssim_score,
                        "difference_percentage": comp.difference_percentage,
                    },
                    "metadata_diff": comp.metadata_diff,
                    "differential_regions": comp.differential_regions,
                    "summary": comp.summary,
                }

        # 3. Retrieve Custody Audit Logs
        stmt = (
            select(ExhibitCustodyLog)
            .where(ExhibitCustodyLog.document_id == document.id)
            .order_by(ExhibitCustodyLog.timestamp.asc())
        )
        logs = db.scalars(stmt).all()
        custody_logs = [
            {
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "event_type": l.event_type,
                "status": l.status,
                "sha256_hash": l.sha256_hash,
                "ip_address": l.ip_address,
            }
            for l in logs
        ]

        document_meta = {
            "id": document.id,
            "original_filename": document.original_filename,
            "file_type": document.file_type,
            "size_bytes": document.size_bytes,
            "page_count": document.page_count or 1,
            "sha256_hash": document.sha256_hash or "",
            "case_id": document.case_id,
        }

        # 4. Generate PDF bytes
        pdf_bytes = self.builder.build_report(
            report_number=report_number,
            document_meta=document_meta,
            analysis_data=analysis_data,
            custody_logs=custody_logs,
            comparison_data=comp_data,
            analyst_notes=analyst_notes,
            analyst_name=user_name,
            analyst_role=user_role,
        )

        # 5. Calculate Cryptographic Hash
        report_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        # 6. Save to Isolated Reports Directory
        report_dir = Path(self.settings.reports_dir).resolve() / report_id
        report_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = report_dir / f"{report_number}.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # 7. Record Custody Event
        AuditService.record_custody_event(
            db,
            document_id=document.id,
            event_type="REPORT_GENERATED",
            sha256_hash=report_sha256,
            user_id=user_id,
            status="VERIFIED",
            ip_address=client_ip,
            details={
                "report_id": report_id,
                "report_number": report_number,
                "pdf_size_bytes": len(pdf_bytes),
                "comparison_included": bool(comp_data),
            },
        )

        # 8. Persist Report Entity
        repo = ReportRepository(db)
        rep = repo.create_report(
            report_id=report_id,
            report_number=report_number,
            document_id=document.id,
            user_id=user_id,
            comparison_id=comparison_id if comp_data else None,
            title=title or f"Forensic Examination: {document.original_filename}",
            file_path=str(pdf_path),
            sha256_hash=report_sha256,
            file_size_bytes=len(pdf_bytes),
            page_count=len(PdfReader(io.BytesIO(pdf_bytes)).pages),
            analysis_version=analysis_data.get("analysis_version", 1),
            analyst_notes=analyst_notes,
            metadata_snapshot={
                "unified_risk_tier": analysis_data.get("unified_risk_tier"),
                "overall_verdict": analysis_data.get("overall_verdict"),
                "ml_probability": analysis_data.get("track_1_ml", {}).get("forgery_probability"),
                "composite_risk_score": analysis_data.get("composite_risk_score"),
                "document_name": document.original_filename,
            },
        )

        return rep

    def get_report_file(
        self,
        db: Session,
        report_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[Path, str, str]:
        """
        Retrieves a report file for download, verifying integrity and logging the event.
        Returns: (file_path, report_number, sha256_hash).
        """
        client_ip = ip_address or "127.0.0.1"
        repo = ReportRepository(db)
        rep = repo.get_report(report_id)
        if not rep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Forensic report '{report_id}' not found.",
            )

        file_path = Path(rep.file_path).resolve()
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file '{rep.report_number}.pdf' missing from storage archive.",
            )

        # Cryptographic Integrity Verification before serving
        if not verify_file_integrity(file_path, rep.sha256_hash):
            AuditService.record_custody_event(
                db,
                document_id=rep.document_id,
                event_type="TAMPERING_ALARM",
                sha256_hash=rep.sha256_hash,
                user_id=user_id,
                status="TAMPERED",
                ip_address=client_ip,
                details={
                    "action": "report_download_aborted",
                    "report_id": rep.id,
                    "reason": "Report PDF modified post-generation. SHA-256 hash mismatch.",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="TAMPERING_ALARM: Report file integrity check failed. Stored PDF does not match immutable hash.",
            )

        # Record download event in custody log
        AuditService.record_custody_event(
            db,
            document_id=rep.document_id,
            event_type="REPORT_DOWNLOADED",
            sha256_hash=rep.sha256_hash,
            user_id=user_id,
            status="VERIFIED",
            ip_address=client_ip,
            details={"report_id": rep.id, "report_number": rep.report_number},
        )

        return file_path, rep.report_number, rep.sha256_hash
