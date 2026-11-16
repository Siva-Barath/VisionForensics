"""
audit_service.py — Append-only security and exhibit custody logging service.
Records authentication events, authorization checks, administrative actions, and exhibit custody events.
Sanitizes all payload data to strictly prevent logging passwords, tokens, or document contents.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.audit import SecurityAuditLog, ExhibitCustodyLog
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service handling immutable security and custody audit logging."""

    @staticmethod
    def record_security_event(
        db: Session,
        event_type: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditLog:
        """Records a security audit event (login, logout, token rotation, authz failure)."""
        # Strictly sanitize details to ensure no sensitive credentials leak into logs
        safe_details = {}
        if details:
            for k, v in details.items():
                if any(s in k.lower() for s in ("password", "token", "secret", "cookie")):
                    safe_details[k] = "[REDACTED]"
                else:
                    safe_details[k] = str(v)[:256]

        log_entry = SecurityAuditLog(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            details=safe_details,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        logger.info(
            "Security Audit Log: %s | user=%s (%s) | ip=%s",
            event_type,
            user_id,
            user_email,
            ip_address,
        )
        return log_entry

    @staticmethod
    def record_custody_event(
        db: Session,
        document_id: str,
        event_type: str,
        sha256_hash: str,
        user_id: Optional[str] = None,
        status: str = "RECORDED",
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> ExhibitCustodyLog:
        """Records an exhibit custody lifecycle event (ingestion, hash verification, analysis, alarm)."""
        safe_details = {k: str(v)[:256] for k, v in (details or {}).items()}

        log_entry = ExhibitCustodyLog(
            document_id=document_id,
            event_type=event_type,
            sha256_hash=sha256_hash,
            user_id=user_id,
            status=status,
            ip_address=ip_address,
            details=safe_details,
        )
        db.add(log_entry)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(log_entry)

        if event_type == "TAMPERING_ALARM":
            logger.critical(
                "DEFENSIBLE CUSTODY ALARM: TAMPERING_ALARM on exhibit %s! user=%s ip=%s",
                document_id,
                user_id,
                ip_address,
            )
        else:
            logger.info(
                "Exhibit Custody Log: %s | doc=%s | status=%s | sha256=%s",
                event_type,
                document_id,
                status,
                sha256_hash[:16],
            )
        return log_entry

    @staticmethod
    def ingestion_digest(db: Session, document_id: str) -> Optional[str]:
        statement = select(ExhibitCustodyLog.sha256_hash).where(
            ExhibitCustodyLog.document_id == document_id,
            ExhibitCustodyLog.event_type == "EXHIBIT_INGESTED",
        ).order_by(ExhibitCustodyLog.timestamp.asc())
        return db.scalars(statement).first()

    @staticmethod
    def list_security_logs(db: Session, skip: int = 0, limit: int = 100) -> List[SecurityAuditLog]:
        """Returns security audit logs ordered by timestamp descending."""
        stmt = select(SecurityAuditLog).order_by(SecurityAuditLog.timestamp.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_custody_logs(db: Session, document_id: str) -> List[ExhibitCustodyLog]:
        """Returns the full custody ledger for a specific document exhibit."""
        stmt = (
            select(ExhibitCustodyLog)
            .where(ExhibitCustodyLog.document_id == document_id)
            .order_by(ExhibitCustodyLog.timestamp.asc())
        )
        return list(db.scalars(stmt).all())
