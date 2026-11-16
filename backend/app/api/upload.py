from fastapi import APIRouter, UploadFile, File, Request, Depends, Form
from typing import Optional, Literal
from sqlalchemy.orm import Session

from app.schemas.document import UploadResponse
from app.core.logging import get_logger
from app.core.auth import get_current_active_user
from app.core.rate_limiter import limiter
from app.core.network import get_client_ip
from app.config.settings import get_settings
from app.database.session import get_db
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a document for forensic analysis",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="PDF, PNG, JPG, or JPEG document"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    case_title: Optional[str] = Form(None, max_length=255),
    case_notes: Optional[str] = Form(None, max_length=10000),
    priority: Literal['routine', 'urgent'] = Form('routine'),
) -> UploadResponse:
    """
    Accepts a document upload, enforces rate limiting, associates with authenticated user,
    and runs it through the forensic analysis pipeline.
    """
    from app import document_service  # import here to avoid circular import at module load

    settings = get_settings()
    client_ip = get_client_ip(request)

    # Enforce sliding-window rate limit (10 uploads per minute per IP)
    limiter.enforce(
        f"upload:{client_ip}",
        max_requests=settings.rate_limit_upload_per_minute,
        window_seconds=60,
    )

    context = await document_service.ingest(
        file=file,
        uploader_id=current_user.id if current_user else None,
        ip_address=client_ip,
        case_details={"title": case_title.strip(), "notes": case_notes, "priority": priority} if case_title and case_title.strip() else None,
    )

    return UploadResponse(
        job_id=context.job_id,
        document_id=context.document_id,
        filename=context.stored_path.name if context.stored_path else "",
        original_filename=context.original_filename,
        path=str(context.stored_path) if context.stored_path else "",
        type=context.file_type,
        size_bytes=context.size_bytes,
        status=context.document_status,
        processing_status=context.pipeline_status,
        pipeline_stage=context.current_stage,
        page_count=context.page_count,
        pages=context.page_images or None,
        warnings=context.warnings,
        processing_time_ms=context.processing_time_ms,
    )
