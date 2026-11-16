"""
reports.py — API endpoints for forensic investigation report generation, listing, and download.
Enforces document ownership, role-based access control, cryptographic hash validation,
and chain-of-custody audit logging.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.core.auth import get_current_active_user, check_document_access
from app.core.network import get_client_ip
from app.schemas.report import (
    ReportGenerationRequest,
    ReportSummaryResponse,
    ReportDetailResponse,
)
from app.repositories.report_repository import ReportRepository
from app.repositories.comparison_repository import ComparisonRepository
from app.services.report_service import ReportService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Forensic Reports"])
_report_service = ReportService()


@router.post(
    "",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a defense-grade forensic PDF investigation report",
)
async def generate_report(
    payload: ReportGenerationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReportDetailResponse:
    """
    Compiles, persists, and hashes a comprehensive PDF investigation report.
    Enforces object-level authorization on the document and any linked comparison.
    """
    client_ip = get_client_ip(request)

    # 1. Enforce IDOR protection on primary document
    doc = check_document_access(payload.document_id, current_user, db, request)

    # 2. If comparison is linked, verify access to both parent exhibits
    if payload.comparison_id and payload.include_comparison:
        comp_repo = ComparisonRepository(db)
        comp = comp_repo.get_comparison(payload.comparison_id)
        if not comp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked comparison record '{payload.comparison_id}' not found.",
            )
        check_document_access(comp.document_a_id, current_user, db, request)
        check_document_access(comp.document_b_id, current_user, db, request)

    # 3. Generate and store PDF report
    rep = _report_service.generate_report(
        db=db,
        document=doc,
        user_id=current_user.id,
        comparison_id=payload.comparison_id if payload.include_comparison else None,
        title=payload.title,
        analyst_notes=payload.analyst_notes,
        user_name=current_user.full_name or "Forensic Analyst",
        user_role=current_user.role,
        ip_address=client_ip,
    )

    return ReportDetailResponse(
        report_id=rep.id,
        report_number=rep.report_number,
        document_id=rep.document_id,
        title=rep.title,
        status=rep.status,
        sha256_hash=rep.sha256_hash,
        file_size_bytes=rep.file_size_bytes,
        page_count=rep.page_count,
        analysis_version=rep.analysis_version,
        analyst_notes=rep.analyst_notes,
        metadata_snapshot=rep.metadata_snapshot,
        download_url=f"/api/v1/reports/{rep.id}/download",
        created_at=rep.created_at.isoformat(),
    )


@router.get(
    "/{report_id}",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve forensic report metadata",
)
async def get_report_detail(
    report_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReportDetailResponse:
    """
    Retrieves metadata for an existing forensic report, verifying caller access to exhibit.
    """
    repo = ReportRepository(db)
    rep = repo.get_report(report_id)
    if not rep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forensic report '{report_id}' not found.",
        )

    # Enforce access to underlying document
    check_document_access(rep.document_id, current_user, db, request)

    return ReportDetailResponse(
        report_id=rep.id,
        report_number=rep.report_number,
        document_id=rep.document_id,
        title=rep.title,
        status=rep.status,
        sha256_hash=rep.sha256_hash,
        file_size_bytes=rep.file_size_bytes,
        page_count=rep.page_count,
        analysis_version=rep.analysis_version,
        analyst_notes=rep.analyst_notes,
        metadata_snapshot=rep.metadata_snapshot,
        download_url=f"/api/v1/reports/{rep.id}/download",
        created_at=rep.created_at.isoformat(),
    )


@router.get(
    "/{report_id}/download",
    summary="Download verified forensic investigation PDF report",
)
async def download_report_pdf(
    report_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Streams the verified PDF report file, strictly confirming SHA-256 hash integrity
    and recording the REPORT_DOWNLOADED custody event.
    """
    client_ip = get_client_ip(request)
    repo = ReportRepository(db)
    rep = repo.get_report(report_id)
    if not rep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forensic report '{report_id}' not found.",
        )

    # Enforce access to underlying document exhibit
    check_document_access(rep.document_id, current_user, db, request)

    file_path, report_number, sha256_hash = _report_service.get_report_file(
        db=db,
        report_id=report_id,
        user_id=current_user.id,
        ip_address=client_ip,
    )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{report_number}.pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{report_number}.pdf"',
            "X-Report-SHA256": sha256_hash,
            "Cache-Control": "private, no-cache, no-store, must-revalidate",
        },
    )


@router.get(
    "",
    response_model=List[ReportSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List available forensic reports",
)
async def list_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ReportSummaryResponse]:
    """
    Lists recent forensic reports accessible to the current authenticated analyst.
    """
    repo = ReportRepository(db)
    all_reports = repo.list_reports(limit=limit, offset=offset)

    # Filter reports by user accessibility (admins see all, analysts see their own or assigned)
    accessible = []
    for r in all_reports:
        try:
            check_document_access(r.document_id, current_user, db, request)
            accessible.append(
                ReportSummaryResponse(
                    report_id=r.id,
                    report_number=r.report_number,
                    document_id=r.document_id,
                    document_name=r.metadata_snapshot.get("document_name", r.document.original_filename if r.document else "Exhibit"),
                    title=r.title,
                    status=r.status,
                    sha256_hash=r.sha256_hash,
                    file_size_bytes=r.file_size_bytes,
                    page_count=r.page_count,
                    unified_risk_tier=r.metadata_snapshot.get("unified_risk_tier", "UNKNOWN"),
                    overall_verdict=r.metadata_snapshot.get("overall_verdict", "INCONCLUSIVE"),
                    ml_probability=r.metadata_snapshot.get("ml_probability"),
                    download_url=f"/api/v1/reports/{r.id}/download",
                    created_at=r.created_at.isoformat(),
                )
            )
        except HTTPException:
            continue

    return accessible
