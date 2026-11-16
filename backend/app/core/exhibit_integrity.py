"""Fail-closed access guard for original exhibits and their derived results."""
from pathlib import Path

from fastapi import HTTPException

from app.core.security import verify_file_integrity
from app.services.audit_service import AuditService


def require_exhibit_integrity(document, db, user_id=None, ip_address=None) -> Path:
    path = Path(document.file_path) if document.file_path else None
    recorded_digest = AuditService.ingestion_digest(db, document.id)
    if path is None or not path.is_file():
        event, state, code, detail = (
            "EXHIBIT_MISSING", "MISSING", 410,
            "The original exhibit is missing from storage. Derived results cannot be verified.",
        )
    elif not document.sha256_hash or not recorded_digest:
        event, state, code, detail = (
            "INTEGRITY_UNVERIFIABLE", "UNVERIFIABLE", 409,
            "The original exhibit has no verifiable ingestion SHA-256 custody record. Integrity cannot be verified.",
        )
    elif document.sha256_hash != recorded_digest or not verify_file_integrity(path, recorded_digest):
        event, state, code, detail = (
            "TAMPERING_ALARM", "TAMPERED", 409,
            "TAMPERING_ALARM: Original exhibit SHA-256 does not match its recorded digest. Access aborted.",
        )
    else:
        return path
    AuditService.record_custody_event(
        db, document_id=document.id, event_type=event,
        sha256_hash=document.sha256_hash or "", user_id=user_id,
        status=state, ip_address=ip_address, details={"reason": detail},
    )
    raise HTTPException(status_code=code, detail=detail)
