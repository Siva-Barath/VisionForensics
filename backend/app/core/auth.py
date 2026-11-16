"""
auth.py — Authentication and Authorization dependencies for FastAPI endpoints.
Enforces JWT validation, active account verification, Role-Based Access Control (RBAC),
and object-level ownership checks (IDOR prevention).
"""

from __future__ import annotations
from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import decode_access_token
from app.core.permissions import UserRole
from app.models.user import User
from app.models.document import Document
from app.models.case import Case
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.core.network import get_client_ip
from app.core.logging import get_logger
import jwt

logger = get_logger(__name__)

# Optional HTTP Bearer security scheme
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts, decodes, and validates the JWT access token from Authorization header or cookie.
    Authentication is required in every environment. Query-string tokens are rejected.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    user_repo = UserRepository(db)

    # 1. Token provided — validate rigorously
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims: missing subject identifier.",
                )
            user = user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account associated with this token no longer exists.",
                )
            return user

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has expired. Please refresh your session.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.PyJWTError, Exception) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Strict production requirement
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    """Verifies that the authenticated user account is active."""
    if not current_user.is_active:
        client_ip = get_client_ip(request)
        AuditService.record_security_event(
            db,
            event_type="AUTHZ_FAILURE",
            user_id=current_user.id,
            user_email=current_user.email,
            ip_address=client_ip,
            details={"reason": "Inactive account access attempt"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact your system administrator.",
        )
    return current_user


def require_role(allowed_roles: List[str]) -> Callable:
    """Factory creating endpoint dependencies that enforce specific RBAC roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
        request: Request = None,
    ) -> User:
        if current_user.role not in allowed_roles:
            client_ip = get_client_ip(request)
            AuditService.record_security_event(
                db,
                event_type="AUTHZ_FAILURE",
                user_id=current_user.id,
                user_email=current_user.email,
                ip_address=client_ip,
                details={
                    "required_roles": allowed_roles,
                    "user_role": current_user.role,
                    "endpoint": str(request.url.path) if request else "",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {allowed_roles}",
            )
        return current_user

    return role_checker


def check_document_access(
    document_id: str,
    user: User,
    db: Session,
    request: Request = None,
) -> Document:
    """
    Enforces object-level authorization and prevents Insecure Direct Object Reference (IDOR).
    Access is granted if:
      - User is a SYSTEM_ADMINISTRATOR, OR
      - User uploaded the document exhibit (uploader_id == user.id), OR
      - Document is attached to a case assigned to or lead by the user, OR
      - User is a SENIOR_INVESTIGATOR.
    """
    repo = DocumentRepository(db)
    doc = repo.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document exhibit '{document_id}' not found or session has expired.",
        )

    # 1. System Administrator has global oversight
    if user.role == UserRole.SYSTEM_ADMINISTRATOR.value:
        return doc

    # 2. Uploader owns the document
    if doc.uploader_id == user.id:
        return doc

    # 3. Case-level assignment check
    if doc.case_id:
        case = db.get(Case, doc.case_id)
        if case:
            if user.role == UserRole.SENIOR_INVESTIGATOR.value:
                return doc
            if case.lead_investigator_id == user.id:
                return doc

    # Access Denied
    client_ip = get_client_ip(request)
    AuditService.record_security_event(
        db,
        event_type="AUTHZ_FAILURE",
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
        details={
            "target_document_id": document_id,
            "document_uploader_id": doc.uploader_id,
            "user_role": user.role,
            "reason": "Cross-user document access denied",
        },
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You do not have permission to view or manage this document exhibit.",
    )
