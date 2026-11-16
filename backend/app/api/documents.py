"""
documents.py — API routes for document analysis retrieval, exhibit image serving,
and chain of custody audit logs. Enforces role-based authorization, IDOR defense,
and cryptographic SHA-256 exhibit integrity checks before retrieval.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.models.user import User
from app.core.auth import get_current_active_user, check_document_access
from app.core.exhibit_integrity import require_exhibit_integrity
from app.core.security import verify_file_integrity
from app.services.module_status import module_statuses
from app.core.network import get_client_ip
from app.services.audit_service import AuditService
from app.schemas.document import DocumentListItem
from app.schemas.analysis import (
    DocumentAnalysisResponse,
    Track1MLSummary,
    RawMLResult,
    Track2SymbolicSummary,
    PageMLSummary,
    VisualEvidenceSummary,
    CompressionQualificationSummary,
    DecisionTraceItem,
    ForensicLimitationItem,
    DetectedRegionResponse,
    BoundingBoxResponse,
    DocumentDimensions,
    PageDimension,
)
from app.schemas.auth import CustodyLogResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Documents"])


@router.get('/documents/{document_id}/heatmap', summary='Verified derived ELA error map')
async def get_ela_heatmap(document_id: str, request: Request, page: int = Query(0, ge=0),
                          current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    from app import document_service
    doc = check_document_access(document_id, current_user, db, request)
    require_exhibit_integrity(doc, db, current_user.id, get_client_ip(request))
    context = document_service.get_context(document_id)
    artifacts = context.artifacts if context else []
    artifact = next((item for item in artifacts if item.type == 'ela_heatmap' and item.page_index == page), None)
    if artifact is None or not Path(artifact.path).is_file():
        raise HTTPException(404, 'No ELA heatmap was retained for this page')
    if not artifact.sha256_hash or not verify_file_integrity(Path(artifact.path), artifact.sha256_hash):
        raise HTTPException(409, 'Derived ELA heatmap integrity verification failed')
    return FileResponse(artifact.path, media_type='image/png')


@router.get("/documents/{document_id}/original", summary="Download the verified original exhibit")
async def get_original_document(
    document_id: str, request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    doc = check_document_access(document_id, current_user, db, request)
    client_ip = get_client_ip(request)
    path = require_exhibit_integrity(doc, db, current_user.id, client_ip)
    AuditService.record_custody_event(
        db, document_id=doc.id, event_type="ORIGINAL_DOWNLOADED",
        sha256_hash=doc.sha256_hash, user_id=current_user.id,
        status="VERIFIED", ip_address=client_ip,
    )
    return FileResponse(path, filename=doc.original_filename, media_type="application/octet-stream")


@router.get(
    "/documents/{document_id}/analysis",
    response_model=DocumentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve completed forensic analysis and ML predictions",
)
async def get_document_analysis(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DocumentAnalysisResponse:
    """
    Retrieves the completed forensic analysis for an uploaded document,
    enforcing role-based authorization, IDOR protection, and SHA-256 exhibit
    integrity verification before returning analysis data.
    """
    from app import document_service

    client_ip = get_client_ip(request)

    # 1. Enforce Object-Level Access Control (IDOR Prevention)
    doc = check_document_access(document_id, current_user, db, request)

    # 2. Cryptographic Exhibit Integrity Verification
    require_exhibit_integrity(doc, db, current_user.id, client_ip)

    context = document_service.get_context(document_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document analysis for '{document_id}' not found or has expired.",
        )

    # Record verified custody access event
    AuditService.record_custody_event(
        db,
        document_id=document_id,
        event_type="EXHIBIT_ACCESSED",
        sha256_hash=doc.sha256_hash or "",
        user_id=current_user.id if current_user else None,
        status="VERIFIED",
        ip_address=client_ip,
        details={"action": "analysis_retrieval"},
    )

    # 4. Extract Track 1 ML Summary
    ml_pred = context.ml_prediction or {}
    track_1_ml = Track1MLSummary(
        available=ml_pred.get("status") in ("SUCCESS", "DEGRADED"),
        status=ml_pred.get("status", "UNAVAILABLE"),
        forgery_probability=ml_pred.get("forgery_probability"),
        predicted_class=ml_pred.get("predicted_class"),
        feature_vector=ml_pred.get("feature_vector", {}),
        risk_tier=ml_pred.get("risk_tier", "UNKNOWN"),
        operational_threshold=ml_pred.get("operational_threshold", 0.40),
        feature_completeness=ml_pred.get("feature_completeness", 1.0),
        imputed_features=ml_pred.get("imputed_features", {}),
        top_contributing_features=ml_pred.get("top_contributing_features", {}),
    )

    # 5. Extract Track 2 Symbolic Summary
    risk_assessment = context.risk_assessment or {}
    t2 = risk_assessment.get("track_2_symbolic", {})
    track_2_symbolic = Track2SymbolicSummary(
        available=t2.get("available", True),
        symbolic_severity_score=t2.get("symbolic_severity_score", 0.0),
        symbolic_evidence=t2.get("symbolic_evidence", []),
    )

    # 5b. Extract Track 3 Visual Evidence Summary (REM-03)
    t3 = risk_assessment.get("track_3_visual") or getattr(context, "visual_evidence", None) or {}
    track_3_visual = VisualEvidenceSummary(
        available=t3.get("available", False),
        detected_clusters=t3.get("detected_clusters", 0),
        max_cluster_confidence=t3.get("max_cluster_confidence", 0.0),
        total_inlier_matches=t3.get("total_inlier_matches", 0),
        copy_move_confirmed=t3.get("copy_move_confirmed", False),
        visual_tier=t3.get("visual_tier", "LOW_RISK"),
        evidence_items=t3.get("evidence_items", []),
    )

    # 5c. Extract Compression Qualification Summary (REM-04)
    cq = risk_assessment.get("compression_qualification") or getattr(context, "compression_qualification", None) or {}
    compression_qualification = CompressionQualificationSummary(
        is_jpeg=cq.get("is_jpeg", False),
        estimated_quality=cq.get("estimated_quality"),
        is_heavily_compressed=cq.get("is_heavily_compressed", False),
        compression_notice=cq.get("compression_notice"),
    )

    # 5d. Extract Per-Page ML Summaries (REM-01)
    pages_ml = [
        PageMLSummary(
            page_index=p.get("page_index", idx),
            forgery_probability=p.get("forgery_probability"),
            predicted_class=p.get("predicted_class"),
            risk_tier=p.get("risk_tier", "UNKNOWN"),
            status=p.get("status", "SUCCESS"),
            feature_completeness=p.get("feature_completeness", 1.0),
            top_contributing_features=p.get("top_contributing_features", {}),
        )
        for idx, p in enumerate(getattr(context, "pages_ml", []) or [])
    ]
    if not pages_ml and track_1_ml.available:
        pages_ml = [
            PageMLSummary(
                page_index=0,
                forgery_probability=track_1_ml.forgery_probability,
                predicted_class=track_1_ml.predicted_class,
                risk_tier=track_1_ml.risk_tier,
                status=track_1_ml.status,
                feature_completeness=track_1_ml.feature_completeness,
                top_contributing_features=track_1_ml.top_contributing_features,
            )
        ]

    # 6. Decision Trace
    raw_trace = risk_assessment.get("decision_trace", [])
    decision_trace = [
        DecisionTraceItem(
            track=step.get("track", ""),
            finding=step.get("finding", ""),
            description=step.get("description"),
            evidence_items=step.get("evidence_items"),
            features_considered=step.get("features_considered"),
        )
        for step in raw_trace
    ]

    # 7. Limitations
    raw_limits = ml_pred.get("limitations", [])
    limitations = [
        ForensicLimitationItem(
            code=item.get("code", "NOTICE"),
            severity=item.get("severity", "INFO"),
            message=item.get("message", ""),
        )
        for item in raw_limits
    ]

    # 8. Detected Visual Regions
    def _sanitize_points(pts):
        if not pts:
            return []
        sanitized = []
        for pt in pts:
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                try:
                    sanitized.append([round(float(pt[0]), 2), round(float(pt[1]), 2)])
                except (ValueError, TypeError):
                    pass
        return sanitized

    detected_regions = [
        DetectedRegionResponse(
            id=str(r.get("id", f"region_{i}")),
            evidence_id=r.get("evidence_id"),
            detector=str(r.get("detector", "unknown")),
            category=str(r.get("category", "UNKNOWN")),
            severity=float(r.get("severity", 0.0)),
            confidence=float(r.get("confidence", 1.0)),
            description=str(r.get("description", "")),
            page_index=int(r.get("page_index", 0)),
            bounding_box=BoundingBoxResponse(
                points=_sanitize_points(r.get("bounding_box", {}).get("points", []))
            ),
        )
        for i, r in enumerate(context.detected_regions or [])
    ]

    # 9. Document Dimensions & Multi-Page Geometry
    from app.repositories.document_repository import DocumentRepository
    repo = DocumentRepository(db)
    db_pages = repo.get_document_pages(document_id)
    page_dims: List[PageDimension] = []

    if db_pages:
        for p in db_pages:
            w, h = p.width, p.height
            if (w == 0 or h == 0) and p.image_path:
                try:
                    from PIL import Image
                    p_img = Path(p.image_path)
                    if p_img.exists():
                        with Image.open(p_img) as img:
                            w, h = img.width, img.height
                except Exception:
                    pass
            page_dims.append(PageDimension(
                page_index=p.page_index,
                width=w or 800,
                height=h or 1000,
                dpi=p.dpi or 200,
            ))
    elif context.quality_metrics:
        for idx, qm in enumerate(context.quality_metrics):
            page_dims.append(PageDimension(
                page_index=idx,
                width=qm.width or 800,
                height=qm.height or 1000,
                dpi=200,
            ))
    elif context.preprocessed_images or context.page_images:
        imgs = context.preprocessed_images or context.page_images
        for idx, img_path_str in enumerate(imgs):
            w, h = 800, 1000
            try:
                from PIL import Image
                p_img = Path(img_path_str)
                if p_img.exists():
                    with Image.open(p_img) as img:
                        w, h = img.width, img.height
            except Exception:
                pass
            page_dims.append(PageDimension(page_index=idx, width=w, height=h, dpi=200))

    if not page_dims:
        page_dims = [PageDimension(page_index=0, width=800, height=1000, dpi=200)]

    image_dimensions = DocumentDimensions(
        width=page_dims[0].width,
        height=page_dims[0].height,
        page_count=context.page_count or len(page_dims),
        pages=page_dims,
    )

    has_preview = bool(context.preprocessed_images or context.page_images or context.stored_path or db_pages)

    return DocumentAnalysisResponse(
        document_id=context.document_id,
        job_id=context.job_id,
        original_filename=context.original_filename,
        file_type=context.file_type,
        status=context.document_status,
        overall_verdict=risk_assessment.get("overall_verdict", "INCONCLUSIVE"),
        unified_risk_tier=risk_assessment.get("unified_risk_tier", "UNKNOWN"),
        risk_description=risk_assessment.get("risk_description", "Analysis pending."),
        composite_risk_score=context.risk_score or 0.0,
        track_1_ml=track_1_ml,
        raw_ml=RawMLResult(available=context.raw_ml_prediction.get("status") in ("SUCCESS", "DEGRADED"), **context.raw_ml_prediction) if context.raw_ml_prediction else None,
        module_statuses=module_statuses(context),
        heatmap_available_pages=[item.page_index for item in context.artifacts if item.type == 'ela_heatmap' and item.page_index is not None],
        track_2_symbolic=track_2_symbolic,
        track_3_visual=track_3_visual,
        compression_qualification=compression_qualification,
        pages_ml=pages_ml,
        decision_trace=decision_trace,
        limitations=limitations,
        warnings=context.warnings,
        processing_time_ms=context.processing_time_ms,
        detected_regions=detected_regions,
        image_dimensions=image_dimensions,
        preview_available=has_preview,
        metadata_info=getattr(context, "metadata", None),
    )


@router.get(
    "/documents/{document_id}/image",
    summary="Retrieve document page image preview",
)
async def get_document_image(
    document_id: str,
    page: int = 0,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Serves the genuine preprocessed page image for the document exhibit.
    Enforces role-based authorization, IDOR protection, and SHA-256 exhibit integrity.
    """
    from app import document_service

    client_ip = get_client_ip(request)

    # 1. Enforce Object-Level Access Control (IDOR Prevention)
    doc = check_document_access(document_id, current_user, db, request)

    # 2. Cryptographic Exhibit Integrity Verification
    require_exhibit_integrity(doc, db, current_user.id, client_ip)

    context = document_service.get_context(document_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found or session has expired.",
        )

    # 3. Validate Page Index
    if page < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid page index {page}. Page index must be greater than or equal to 0.",
        )

    max_pages = context.page_count or (len(context.preprocessed_images) if context.preprocessed_images else 1)
    if page >= max_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page index {page} out of bounds. Document '{document_id}' has {max_pages} page(s).",
        )

    # 4. Resolve Page Image Path
    candidate_paths = []
    if context.preprocessed_images and len(context.preprocessed_images) > page:
        candidate_paths.append(Path(context.preprocessed_images[page]))
    if context.page_images and len(context.page_images) > page:
        candidate_paths.append(Path(context.page_images[page]))

    repo = DocumentRepository(db)
    db_page = repo.get_document_page(document_id, page)
    if db_page and db_page.image_path:
        candidate_paths.append(Path(db_page.image_path))

    # Standard processed directory conventions
    candidate_paths.append(Path("processed") / document_id / f"{document_id}_preprocessed_page_{page}.png")
    candidate_paths.append(Path("/app/processed") / document_id / f"{document_id}_preprocessed_page_{page}.png")

    if page == 0 and context.stored_path:
        candidate_paths.append(Path(context.stored_path))
    if page == 0 and doc.file_path:
        candidate_paths.append(Path(doc.file_path))

    image_path = None
    for cand in candidate_paths:
        if cand.exists():
            image_path = cand
            break
        cand_app = Path("/app") / cand
        if cand_app.exists():
            image_path = cand_app
            break

    if not image_path or not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document image for '{document_id}' page {page} not found on disk.",
        )

    # If the file is TIFF, convert to web-renderable PNG cache so browsers can display it
    if image_path.suffix.lower() in (".tif", ".tiff"):
        png_cache = image_path.with_suffix(".png")
        if not png_cache.exists():
            try:
                from PIL import Image
                with Image.open(image_path) as tiff_im:
                    tiff_im.convert("RGB").save(png_cache, "PNG")
                image_path = png_cache
            except Exception as conv_err:
                logger.warning("Could not convert TIFF to PNG for browser preview: %s", conv_err)
        else:
            image_path = png_cache


    # Record exhibit image accessed
    AuditService.record_custody_event(
        db,
        document_id=document_id,
        event_type="EXHIBIT_IMAGE_ACCESSED",
        sha256_hash=doc.sha256_hash or "",
        user_id=current_user.id if current_user else None,
        status="VERIFIED",
        ip_address=client_ip,
        details={"page": page},
    )

    suffix = image_path.suffix.lower()
    media_type = "image/png" if suffix in (".png", ".webp") else "image/jpeg"
    return FileResponse(
        path=str(image_path),
        media_type=media_type,
        filename=f"{document_id}_page_{page}{suffix}",
    )


@router.get(
    "/documents/{document_id}/custody-logs",
    response_model=List[CustodyLogResponse],
    summary="Retrieve defensible chain of custody history for an exhibit",
)
async def get_document_custody_logs(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[CustodyLogResponse]:
    """
    Retrieves the complete immutable chain of custody ledger for a specific document exhibit.
    Restricted to authorized users for that exhibit.
    """
    # Enforce Object-Level Access Control
    _ = check_document_access(document_id, current_user, db, request)
    return AuditService.list_custody_logs(db, document_id)


@router.get(
    "/documents",
    response_model=List[DocumentListItem],
    summary="List document exhibits accessible to the analyst",
)
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[DocumentListItem]:
    """
    Lists recent document exhibits accessible to the authenticated analyst.
    Enforces role-based filtering (administrators see all, analysts see their own or assigned).
    """
    from app.repositories.document_repository import DocumentRepository
    repo = DocumentRepository(db)
    all_docs = repo.list_documents(skip=skip, limit=limit, user=current_user)

    accessible = []
    for doc in all_docs:
        try:
            check_document_access(doc.id, current_user, db, request)
            # Find latest analysis if available
            verdict = None
            risk_tier = None
            risk_score = None
            if doc.analyses:
                latest = doc.analyses[0]
                verdict = latest.overall_verdict
                risk_tier = latest.unified_risk_tier
                risk_score = latest.composite_risk_score

            accessible.append(
                DocumentListItem(
                    id=doc.id,
                    original_filename=doc.original_filename,
                    file_type=doc.file_type,
                    size_bytes=doc.size_bytes,
                    status=doc.status,
                    page_count=doc.page_count or 1,
                    sha256_hash=doc.sha256_hash,
                    created_at=doc.created_at.isoformat(),
                    uploader_id=doc.uploader_id,
                    overall_verdict=verdict,
                    unified_risk_tier=risk_tier,
                    composite_risk_score=risk_score,
                )
            )
        except HTTPException:
            continue

    return accessible

