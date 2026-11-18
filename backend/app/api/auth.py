"""
auth.py — Authentication, Session, and Role-Based Access Control (RBAC) API routes.
Provides user registration, Argon2id login, JWT token generation, HttpOnly refresh cookies,
refresh rotation, logout revocation, and administrative user/audit management.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.config.settings import get_settings
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.rate_limiter import limiter
from app.core.network import get_client_ip, validate_request_origin
from app.core.auth import (
    get_current_user,
    get_current_active_user,
    require_role,
)
from app.schemas.auth import (
    UserRegisterRequest,
    UserCreateAdminRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    UserStatusUpdateRequest,
    AuditLogResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])
admin_router = APIRouter(prefix="/admin", tags=["Administration & Audit"])


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


# ---------------------------------------------------------------------- #
# Authentication Endpoints                                               #
# ---------------------------------------------------------------------- #

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Public self-registration for forensic analysts.
    Enforces password complexity policy and hashes with Argon2id.
    """
    # 1. Enforce password complexity
    valid_pass, pass_err = validate_password_strength(payload.password)
    if not valid_pass:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pass_err)

    user_repo = UserRepository(db)
    existing = user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # 2. Hash and save
    hashed_pw = hash_password(payload.password)
    user = user_repo.create_user(
        email=payload.email,
        password_hash=hashed_pw,
        full_name=payload.full_name,
        role=UserRole.FORENSIC_ANALYST.value,
        is_active=True,
    )

    client_ip = get_client_ip(request)
    AuditService.record_security_event(
        db,
        event_type="USER_REGISTERED",
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
        details={"role": user.role},
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticates user credentials, sets secure HttpOnly refresh cookie,
    and returns a short-lived (15-minute) JWT access token.
    Enforces sliding-window rate limit (5 attempts per minute per IP).
    """
    settings = get_settings()
    client_ip = get_client_ip(request)
    norm_email = payload.email.strip().lower()

    # 1. Enforce IP sliding-window rate limit
    limiter.enforce(
        f"login:{client_ip}",
        max_requests=settings.rate_limit_login_per_minute,
        window_seconds=60,
    )

    # 2. Enforce Account-level lockout (defense against distributed credential stuffing)
    is_locked, retry_after = limiter.check_account_lockout(
        norm_email,
        max_failed=settings.rate_limit_account_max_failures,
        lockout_seconds=settings.rate_limit_account_lockout_seconds,
    )
    if is_locked:
        AuditService.record_security_event(
            db,
            event_type="LOGIN_ACCOUNT_LOCKED",
            user_id=None,
            user_email=norm_email,
            ip_address=client_ip,
            details={"retry_after": retry_after, "reason": "Excessive failed login attempts"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to excessive failed attempts. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(norm_email)

    # 3. Verify existence and password
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        limiter.record_account_failure(norm_email)
        AuditService.record_security_event(
            db,
            event_type="LOGIN_FAILURE",
            user_id=user.id if user else None,
            user_email=norm_email,
            ip_address=client_ip,
            details={"reason": "Invalid email or password"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful authentication resets account failure counter
    limiter.reset_account(norm_email)

    # 3. Check account activation
    if not user.is_active:
        AuditService.record_security_event(
            db,
            event_type="LOGIN_LOCKED",
            user_id=user.id,
            user_email=user.email,
            ip_address=client_ip,
            details={"reason": "Deactivated account login attempt"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your system administrator.",
        )

    # 4. Generate JWT Access Token (15 mins)
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    # 5. Generate and hash Refresh Token (7 days)
    refresh_token = generate_refresh_token()
    token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    user_repo.save_refresh_token(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    # 6. Set secure cookies (only enforce Secure=True when accessing over HTTPS)
    req_scheme = request.headers.get("x-forwarded-proto", request.url.scheme).lower()
    is_secure_cookie = (req_scheme == "https")
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/",
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )

    AuditService.record_security_event(
        db,
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
        details={"role": user.role},
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Rotates the session refresh token and issues a fresh 15-minute JWT access token.
    Accepts refresh token via HttpOnly cookie or optional JSON body.
    Performs atomic rotation with row-level locking, grace-period concurrency handling,
    and genuine replay attack detection.
    """
    settings = get_settings()
    client_ip = get_client_ip(request)

    using_cookie = False
    raw_token = None
    if payload and payload.refresh_token:
        raw_token = payload.refresh_token
    elif "refresh_token" in request.cookies:
        raw_token = request.cookies.get("refresh_token")
        using_cookie = True

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing. Please log in again.",
        )

    # CSRF check when using cookie authentication
    if using_cookie and not validate_request_origin(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF origin verification failed.",
        )

    user_repo = UserRepository(db)
    token_hash = hash_refresh_token(raw_token)

    # Generate new refresh token and hash
    new_refresh_token = generate_refresh_token()
    new_hash = hash_refresh_token(new_refresh_token)
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    # Execute atomic rotation with row-level lock and grace window evaluation
    success, new_record, user, rot_status = user_repo.rotate_refresh_token_atomic(
        old_token_hash=token_hash,
        new_token_hash=new_hash,
        new_expires_at=new_expires_at,
        grace_window_seconds=settings.refresh_token_grace_window_seconds,
    )

    if rot_status == "NOT_FOUND":
        AuditService.record_security_event(
            db,
            event_type="TOKEN_REUSE_ATTEMPT",
            ip_address=client_ip,
            details={"reason": "Refresh token not found"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if rot_status == "CONCURRENT_ROTATION_GRACE":
        AuditService.record_security_event(
            db,
            event_type="TOKEN_CONCURRENT_COLLISION",
            ip_address=client_ip,
            details={"reason": "Concurrent rotation collision within grace window"},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Token rotation in progress from another concurrent request. Please use the newly issued session token.",
        )

    if rot_status == "REPLAY_BREACH":
        AuditService.record_security_event(
            db,
            event_type="TOKEN_REPLAY_DETECTED",
            ip_address=client_ip,
            details={"action": "Revoked all user sessions"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked refresh token presented. All sessions terminated for security.",
        )

    if rot_status == "EXPIRED":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )

    if rot_status == "USER_INACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated or does not exist.",
        )

    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed.",
        )

    # Issue new access token
    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    # Set rotated cookies (only enforce Secure=True when accessing over HTTPS)
    req_scheme = request.headers.get("x-forwarded-proto", request.url.scheme).lower()
    is_secure_cookie = (req_scheme == "https")
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/",
    )
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )

    AuditService.record_security_event(
        db,
        event_type="TOKEN_ROTATED",
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Revokes the active refresh token and clears the HttpOnly cookie.
    Enforces CSRF origin validation if cookie authentication is used.
    """
    client_ip = get_client_ip(request)
    raw_token = None
    if payload and payload.refresh_token:
        raw_token = payload.refresh_token
    elif "refresh_token" in request.cookies:
        if not validate_request_origin(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF origin verification failed.",
            )
        raw_token = request.cookies.get("refresh_token")

    if raw_token:
        user_repo = UserRepository(db)
        token_hash = hash_refresh_token(raw_token)
        user_repo.revoke_refresh_token(token_hash)

    # Clear cookies
    response.delete_cookie(key="refresh_token", path="/")
    response.delete_cookie(key="access_token", path="/")

    AuditService.record_security_event(
        db,
        event_type="LOGOUT_SUCCESS",
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else None,
        ip_address=client_ip,
    )

    return {"message": "Successfully logged out and revoked session."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Returns profile and role information for currently authenticated user."""
    return current_user


# ---------------------------------------------------------------------- #
# Administrator Management Endpoints                                      #
# ---------------------------------------------------------------------- #

@admin_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    payload: UserCreateAdminRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role([UserRole.SYSTEM_ADMINISTRATOR.value])),
):
    """
    Administrative account creation with explicit role assignment.
    Restricted to SYSTEM_ADMINISTRATOR.
    """
    # 1. Enforce password complexity
    valid_pass, pass_err = validate_password_strength(payload.password)
    if not valid_pass:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pass_err)

    # 2. Check role validity
    if payload.role not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {[r.value for r in UserRole]}",
        )

    user_repo = UserRepository(db)
    if user_repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = user_repo.create_user(
        email=payload.email,
        password_hash=hashed_pw,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )

    client_ip = get_client_ip(request)
    AuditService.record_security_event(
        db,
        event_type="ADMIN_USER_CREATED",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=client_ip,
        details={"created_user_id": user.id, "email": user.email, "role": user.role},
    )

    return user


@admin_router.get("/users", response_model=List[UserResponse])
async def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role([UserRole.SYSTEM_ADMINISTRATOR.value])),
):
    """Lists all user accounts. Restricted to SYSTEM_ADMINISTRATOR."""
    user_repo = UserRepository(db)
    return user_repo.list_users(skip=skip, limit=limit)


@admin_router.put("/users/{user_id}/status", response_model=UserResponse)
async def admin_update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role([UserRole.SYSTEM_ADMINISTRATOR.value])),
):
    """
    Updates user activation status or RBAC role.
    If an account is deactivated, all active sessions and refresh tokens are immediately revoked.
    Restricted to SYSTEM_ADMINISTRATOR.
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_id}' not found.")

    client_ip = get_client_ip(request)

    if payload.role is not None:
        if payload.role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{payload.role}'. Must be one of: {[r.value for r in UserRole]}",
            )
        user = user_repo.update_role(user_id, payload.role)

    if payload.is_active is not None:
        user = user_repo.update_status(user_id, payload.is_active)
        if not payload.is_active:
            # Terminate all active sessions
            user_repo.revoke_all_user_tokens(user_id)
            logger.info("Deactivated user %s and revoked all sessions", user_id)

    AuditService.record_security_event(
        db,
        event_type="ADMIN_USER_UPDATED",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=client_ip,
        details={
            "target_user_id": user_id,
            "is_active": user.is_active,
            "role": user.role,
        },
    )

    return user


@admin_router.get("/audit-logs", response_model=List[AuditLogResponse])
async def admin_get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role([
        UserRole.SYSTEM_ADMINISTRATOR.value,
        UserRole.SENIOR_INVESTIGATOR.value,
        UserRole.FORENSIC_ANALYST.value,
    ])),
):
    """
    Retrieves the system security and custody audit event logs.
    Accessible to SYSTEM_ADMINISTRATOR, SENIOR_INVESTIGATOR, and FORENSIC_ANALYST.
    """
    return AuditService.list_unified_logs(
        db, skip=skip, limit=limit, category=category, search=search
    )
