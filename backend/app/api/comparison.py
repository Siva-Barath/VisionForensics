"""
comparison.py — API routes for forensic document comparison and differential analysis.
Enforces dual-document role-based access control, IDOR defense, exhibit integrity,
and immutable custody logging.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.core.auth import get_current_active_user, check_document_access
from app.core.network import get_client_ip
from app.schemas.comparison import (
    ComparisonRequest,
    ComparisonResponse,
    ComparisonAlignmentResponse,
    ComparisonMetricsResponse,
    DifferentialRegionResponse,
    ComparisonBoundingBox,
    ComparisonMetadataDiff,
    ComparisonDocumentMetadata,
    ComparisonSummaryResponse,
)
from app.repositories.comparison_repository import ComparisonRepository
from app.services.comparison_service import ComparisonService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/comparison", tags=["Document Comparison"])
_comparison_service = ComparisonService()


@router.post(
    "",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform forensic differential comparison between two exhibits",
)
async def perform_comparison(
    payload: ComparisonRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    """
    Performs forensic comparison between Document A and Document B.
    Enforces ownership and RBAC on BOTH documents to prevent cross-case or cross-user IDOR.
    """
    client_ip = get_client_ip(request)

    # 1. Enforce IDOR protection on both documents
    doc_a = check_document_access(payload.document_a_id, current_user, db, request)
    doc_b = check_document_access(payload.document_b_id, current_user, db, request)

    # 2. Execute comparison service
    result = _comparison_service.perform_comparison(
        db=db,
        document_a=doc_a,
        document_b=doc_b,
        page_a=payload.page_a,
        page_b=payload.page_b,
        align_images=payload.align_images,
        user_id=current_user.id,
        ip_address=client_ip,
    )

    return ComparisonResponse(**result)


@router.get(
    "/{comparison_id}",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve completed document comparison analysis",
)
async def get_comparison(
    comparison_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    """
    Retrieves an existing comparison record, verifying that the authenticated user
    holds legitimate access rights to both parent document exhibits.
    """
    repo = ComparisonRepository(db)
    comp = repo.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison analysis '{comparison_id}' not found.",
        )

    # Enforce access to both documents
    check_document_access(comp.document_a_id, current_user, db, request)
    check_document_access(comp.document_b_id, current_user, db, request)

    artifact_urls = {
        "diff_heatmap": f"/api/v1/comparison/{comparison_id}/artifacts/diff_heatmap",
        "diff_mask": f"/api/v1/comparison/{comparison_id}/artifacts/diff_mask",
        "aligned_b": f"/api/v1/comparison/{comparison_id}/artifacts/aligned_b",
    }

    return ComparisonResponse(
        comparison_id=comp.id,
        document_a_id=comp.document_a_id,
        document_b_id=comp.document_b_id,
        page_a=comp.page_a,
        page_b=comp.page_b,
        alignment=ComparisonAlignmentResponse(
            status=comp.alignment_status,
            confidence=comp.alignment_confidence,
            keypoints_detected_a=comp.summary.get("keypoints_a", 0),
            keypoints_detected_b=comp.summary.get("keypoints_b", 0),
            matches_found=comp.summary.get("matches", 0),
        ),
        metrics=ComparisonMetricsResponse(
            similarity_score=comp.similarity_score,
            ssim_score=comp.ssim_score,
            difference_percentage=comp.difference_percentage,
            differing_pixels=comp.summary.get("differing_pixels", 0),
            total_pixels=comp.summary.get("total_pixels", 0),
        ),
        differential_regions=[
            DifferentialRegionResponse(
                region_id=r.get("region_id", ""),
                category=r.get("category", "CONTENT_DIFFERENCE"),
                bounding_box=ComparisonBoundingBox(**r.get("bounding_box", {})),
                polygon=r.get("polygon", []),
                severity=r.get("severity", 0.5),
                area=r.get("area", 0),
                page_a=r.get("page_a", comp.page_a),
                page_b=r.get("page_b", comp.page_b),
            )
            for r in comp.differential_regions
        ],
        metadata_diff=ComparisonMetadataDiff(
            document_a=ComparisonDocumentMetadata(**comp.metadata_diff.get("document_a", {})),
            document_b=ComparisonDocumentMetadata(**comp.metadata_diff.get("document_b", {})),
            dimension_match=comp.metadata_diff.get("dimension_match", True),
            page_count_match=comp.metadata_diff.get("page_count_match", True),
            format_match=comp.metadata_diff.get("format_match", True),
            hash_match=comp.metadata_diff.get("hash_match", False),
        ),
        summary=ComparisonSummaryResponse(
            verdict_category=comp.verdict_category,
            differential_regions_count=len(comp.differential_regions),
            forensic_caveat=comp.summary.get("forensic_caveat", ""),
        ),
        artifact_urls=artifact_urls,
        created_at=comp.created_at.isoformat(),
    )


@router.get(
    "/{comparison_id}/artifacts/{artifact_type}",
    summary="Stream derived comparison image artifact",
)
async def get_comparison_artifact(
    comparison_id: str,
    artifact_type: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Streams derived comparison artifacts (diff_heatmap, diff_mask, aligned_b),
    guaranteeing authorization and exhibit confidentiality.
    """
    if artifact_type not in ("diff_heatmap", "diff_mask", "aligned_b"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown comparison artifact '{artifact_type}'.",
        )

    repo = ComparisonRepository(db)
    comp = repo.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison '{comparison_id}' not found.",
        )

    # Enforce access to both parent exhibits
    check_document_access(comp.document_a_id, current_user, db, request)
    check_document_access(comp.document_b_id, current_user, db, request)

    artifact_info = comp.artifacts.get(artifact_type)
    if not artifact_info or not artifact_info.get("path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_type}' was not generated for this comparison.",
        )

    file_path = Path(artifact_info["path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact file '{artifact_type}' missing from storage.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=f"{comparison_id}_{artifact_type}.png",
        headers={"Cache-Control": "private, max-age=3600"},
    )
