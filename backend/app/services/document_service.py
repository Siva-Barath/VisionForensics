"""
DocumentService — the single entry point for document ingestion and retrieval.

Backed by persistent PostgreSQL storage through DocumentRepository while maintaining
an in-memory L1 cache for sub-millisecond retrieval.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile

from app.pipeline.context import AnalysisContext
from app.pipeline.pipeline import PipelineManager
from app.utils.file_validator import validate_upload
from app.config.settings import Settings
from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.core.exceptions import VisionForensicsError
from app.services.context_snapshot import snapshot_context, restore_context

logger = get_logger(__name__)


class DocumentService:
    def __init__(
        self,
        pipeline: PipelineManager,
        settings: Settings,
        session_factory=SessionLocal,
    ) -> None:
        self._pipeline = pipeline
        self._settings = settings
        self._session_factory = session_factory
        self._analysis_cache: dict[str, AnalysisContext] = {}

    def get_context(self, document_id: str) -> Optional[AnalysisContext]:
        """
        Retrieves completed analysis context by document_id.
        Checks memory L1 cache first; falls back to PostgreSQL persistence on cache miss.
        """
        # 1. L1 Memory Cache
        if document_id in self._analysis_cache:
            return self._analysis_cache[document_id]

        # 2. L2 Persistent PostgreSQL Storage
        try:
            with self._session_factory() as db:
                repo = DocumentRepository(db)
                doc = repo.get_document(document_id)
                if not doc:
                    return None

                analysis = repo.get_latest_analysis(document_id)
                if not analysis:
                    return None

                pages = repo.get_document_pages(document_id)
                page_paths = [p.image_path for p in pages] if pages else []

                # Reconstruct AnalysisContext
                context = AnalysisContext(
                    document_id=doc.id,
                    job_id=analysis.job_id,
                    original_filename=doc.original_filename,
                    file_type=doc.file_type,
                    file_bytes=b"",
                    size_bytes=doc.size_bytes,
                )
                context.stored_path = Path(doc.file_path) if doc.file_path else None
                if analysis.context_snapshot:
                    restore_context(context, analysis.context_snapshot)
                    context.analysis_version = analysis.version
                    self._analysis_cache[document_id] = context
                    return context
                context.document_status = doc.status
                context.page_count = doc.page_count or (len(page_paths) if page_paths else 1)
                context.page_images = page_paths
                context.preprocessed_images = page_paths
                context.warnings = list(analysis.warnings or [])
                context.processing_time_ms = analysis.processing_time_ms
                context.risk_score = analysis.composite_risk_score

                # Reconstruct ML Prediction
                context.ml_prediction = {
                    "available": analysis.ml_available,
                    "status": analysis.ml_status,
                    "forgery_probability": analysis.ml_forgery_probability,
                    "predicted_class": analysis.ml_predicted_class,
                    "risk_tier": "UNKNOWN",  # Legacy storage did not retain the raw ML tier.
                    "operational_threshold": analysis.ml_operational_threshold,
                    "feature_completeness": analysis.ml_feature_completeness,
                    "top_contributing_features": analysis.ml_top_features or {},
                    "imputed_features": analysis.ml_imputed_features or {},
                    "limitations": analysis.limitations or [],
                }

                # Reconstruct Risk Assessment
                context.risk_assessment = {
                    "unified_risk_tier": analysis.unified_risk_tier,
                    "overall_verdict": analysis.overall_verdict,
                    "risk_description": analysis.risk_description or "",
                    "track_2_symbolic": {
                        "available": analysis.symbolic_available,
                        "symbolic_severity_score": analysis.symbolic_severity_score,
                        "symbolic_evidence": analysis.symbolic_evidence or [],
                    },
                    "decision_trace": analysis.decision_trace or [],
                }

                # Reconstruct Detected Regions
                reconstructed_regions = []
                for r in analysis.detected_regions or []:
                    reconstructed_regions.append({
                        "id": r.id,
                        "evidence_id": r.evidence_id,
                        "detector": r.detector,
                        "category": r.category,
                        "severity": float(r.severity),
                        "confidence": float(r.confidence),
                        "description": r.description or "",
                        "page_index": r.page_index,
                        "bounding_box": {
                            "points": r.points_json or []
                        },
                    })
                context.detected_regions = reconstructed_regions
                context.analysis_version = analysis.version
                context.add_warning("Legacy analysis: full per-page results and module execution details were not retained. Missing values are unavailable.")

                # Cache in L1 memory for subsequent queries
                self._analysis_cache[document_id] = context
                logger.debug(
                    "Reconstructed AnalysisContext from PostgreSQL | doc=%s v=%d tier=%s",
                    document_id,
                    analysis.version,
                    analysis.unified_risk_tier,
                )
                return context

        except Exception as exc:
            logger.error("Failed to retrieve document %s from database: %s", document_id, exc)
            raise VisionForensicsError("Stored analysis is temporarily unavailable.", status_code=503) from exc

    async def ingest(
        self,
        file: UploadFile,
        uploader_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        case_details: Optional[Dict[str, Any]] = None,
    ) -> AnalysisContext:
        """
        Validate, store, and begin pipeline processing for an uploaded file.
        Persists document, pages, and versioned analysis results to PostgreSQL.
        """
        # Validate file type and size — raises HTTP-mapped exceptions on failure
        content, file_type = await validate_upload(file, self._settings.max_file_size_bytes)

        # Compute SHA-256 integrity hash immediately upon upload stream receipt
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Build the shared context that will flow through the entire pipeline
        context = AnalysisContext(
            original_filename=file.filename or "upload",
            file_type=file_type,
            file_bytes=content,
            size_bytes=len(content),
        )

        logger.info(
            "Document ingestion started | job=%s document=%s type=%s size=%d sha256=%s uploader=%s",
            context.job_id,
            context.document_id,
            file_type,
            len(content),
            sha256_hash[:16],
            uploader_id,
        )

        # Run the pipeline — always returns context, never raises
        context = await self._pipeline.run(context)

        # Clear raw bytes from context — no longer needed after storage
        context.file_bytes = b""

        # Persist everything to PostgreSQL database
        self._persist_to_database(context, sha256_hash, uploader_id=uploader_id, ip_address=ip_address, case_details=case_details)

        # Cache completed analysis context for query retrieval by document_id
        self._analysis_cache[context.document_id] = context

        return context

    def _persist_to_database(
        self,
        context: AnalysisContext,
        sha256_hash: str,
        uploader_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        case_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist AnalysisContext state into normalized relational database tables and record custody trail."""
        try:
            with self._session_factory() as db:
                repo = DocumentRepository(db, auto_commit=False)
                case_id = None
                if case_details is not None:
                    from app.services.case_service import new_case
                    case = new_case(case_details['title'], case_details.get('notes'), case_details.get('priority', 'routine'), uploader_id)
                    db.add(case)
                    db.flush()
                    case_id = case.id

                # 1. Save Document record
                stored_path_str = str(context.stored_path) if context.stored_path else ""
                stored_name = context.stored_path.name if context.stored_path else ""
                repo.save_document(
                    document_id=context.document_id,
                    original_filename=context.original_filename,
                    stored_filename=stored_name,
                    file_path=stored_path_str,
                    file_type=context.file_type,
                    size_bytes=context.size_bytes,
                    sha256_hash=sha256_hash,
                    page_count=context.page_count or 1,
                    status=context.document_status,
                    uploader_id=uploader_id,
                    case_id=case_id,
                )

                # Record exhibit ingestion custody event
                AuditService.record_custody_event(
                    db,
                    document_id=context.document_id,
                    event_type="EXHIBIT_INGESTED",
                    sha256_hash=sha256_hash,
                    user_id=uploader_id,
                    status="INGESTED",
                    ip_address=ip_address,
                    details={"original_filename": context.original_filename, "size_bytes": context.size_bytes},
                    commit=False,
                )

                # 2. Save Document Pages
                pages_data: List[Dict[str, Any]] = []
                page_paths = context.preprocessed_images or context.page_images
                if page_paths:
                    for idx, p_path in enumerate(page_paths):
                        width, height = 0, 0
                        if context.quality_metrics and len(context.quality_metrics) > idx:
                            qm = context.quality_metrics[idx]
                            width, height = qm.width, qm.height
                        if Path(p_path).is_file():
                            from PIL import Image
                            with Image.open(p_path) as raster:
                                # Region coordinates refer to the derived raster,
                                # which can differ from pre-operation quality size.
                                width, height = raster.size
                        pages_data.append({
                            "page_index": idx,
                            "image_path": p_path,
                            "width": width,
                            "height": height,
                            "dpi": 200,
                        })
                elif context.stored_path and context.file_type != "pdf":
                    pages_data.append({
                        "page_index": 0,
                        "image_path": stored_path_str,
                        "width": 0,
                        "height": 0,
                        "dpi": 200,
                    })

                if pages_data:
                    repo.save_document_pages(context.document_id, pages_data)

                # 3. Extract and Save Analysis Result
                ml_pred = context.ml_prediction or {}
                risk_assessment = context.risk_assessment or {}
                t2 = risk_assessment.get("track_2_symbolic", {})

                # Extract Evidence list and Detected regions
                evidence_list = []
                if context.forgery_report and isinstance(context.forgery_report, dict):
                    evidence_list = context.forgery_report.get("evidence_list", [])

                analysis = repo.save_analysis(
                    document_id=context.document_id,
                    job_id=context.job_id,
                    unified_risk_tier=risk_assessment.get("unified_risk_tier", "UNKNOWN"),
                    overall_verdict=risk_assessment.get("overall_verdict", "INCONCLUSIVE"),
                    risk_description=risk_assessment.get("risk_description"),
                    composite_risk_score=context.risk_score or 0.0,
                    ml_available=ml_pred.get("status") in ("SUCCESS", "DEGRADED"),
                    ml_status=ml_pred.get("status", "UNAVAILABLE"),
                    ml_forgery_probability=ml_pred.get("forgery_probability"),
                    ml_predicted_class=ml_pred.get("predicted_class"),
                    ml_operational_threshold=ml_pred.get("operational_threshold", 0.40),
                    ml_feature_completeness=ml_pred.get("feature_completeness", 1.0),
                    ml_top_features=ml_pred.get("top_contributing_features", {}),
                    ml_imputed_features=ml_pred.get("imputed_features", {}),
                    symbolic_available=t2.get("available", True),
                    symbolic_severity_score=t2.get("symbolic_severity_score", 0.0),
                    symbolic_evidence=t2.get("symbolic_evidence", []),
                    decision_trace=risk_assessment.get("decision_trace", []),
                    limitations=ml_pred.get("limitations", []),
                    warnings=context.warnings,
                    processing_time_ms=context.processing_time_ms,
                    evidence_list=evidence_list,
                    detected_regions=context.detected_regions,
                    context_snapshot=snapshot_context(context),
                )

                # Record analysis execution custody event
                AuditService.record_custody_event(
                    db,
                    document_id=context.document_id,
                    event_type="ANALYSIS_EXECUTED",
                    sha256_hash=sha256_hash,
                    user_id=uploader_id,
                    status=getattr(context.pipeline_status, "value", context.pipeline_status).upper(),
                    ip_address=ip_address,
                    details={
                        "job_id": context.job_id,
                        "unified_risk_tier": risk_assessment.get("unified_risk_tier", "UNKNOWN"),
                        "overall_verdict": risk_assessment.get("overall_verdict", "INCONCLUSIVE"),
                    },
                    commit=False,
                )
                db.commit()
                context.analysis_version = analysis.version

                logger.info(
                    "Successfully persisted document and analysis to PostgreSQL | doc=%s job=%s",
                    context.document_id,
                    context.job_id,
                )

        except Exception as exc:
            logger.error(
                "Database persistence error for document %s: %s",
                context.document_id,
                exc,
                exc_info=True,
            )
            # Exhibit bytes remain on storage for recovery, but a non-durable
            # result must never be cached or acknowledged as a successful upload.
            raise VisionForensicsError(
                "The exhibit was retained, but analysis persistence failed. Contact the administrator with the document reference.",
                status_code=503,
            ) from exc
