"""
security.py — Cryptographic and security primitives for VisionForensics AI.
Handles Argon2id password hashing, JWT access token management, secure refresh token
generation/hashing, and SHA-256 exhibit integrity verification.
"""

from __future__ import annotations
import secrets
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Argon2id password hasher (RFC 9106 recommended profile)
# m=65536 (64 MB memory), t=3 (iterations), p=4 (parallelism)
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


# ---------------------------------------------------------------------- #
# 1. Password Hashing & Validation                                       #
# ---------------------------------------------------------------------- #

def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id with unique salt."""
    return _hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    if not password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforces minimum password complexity requirements:
      - Minimum 8 characters
      - At least one uppercase letter [A-Z]
      - At least one lowercase letter [a-z]
      - At least one digit [0-9]
      - At least one special symbol
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one special character."
    return True, ""


# ---------------------------------------------------------------------- #
# 2. JWT Access Token Management                                         #
# ---------------------------------------------------------------------- #

def create_access_token(
    user_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed, short-lived JWT access token (default 15 minutes)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: Dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises jwt.ExpiredSignatureError if expired, or jwt.PyJWTError if invalid.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp", "iat"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Token is not an access token.")
    return payload


# ---------------------------------------------------------------------- #
# 3. Secure Refresh Token Generation & Hashing                          #
# ---------------------------------------------------------------------- #

def generate_refresh_token() -> str:
    """Generates a cryptographically secure, random URL-safe refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """
    Computes SHA-256 hash of a refresh token.
    Only the hash is persisted in the database; plaintext token is never stored.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------- #
# 4. SHA-256 Exhibit Integrity Verification                             #
# ---------------------------------------------------------------------- #

def compute_bytes_sha256(content: bytes) -> str:
    """Computes SHA-256 digest of in-memory byte content."""
    return hashlib.sha256(content).hexdigest()


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 digest of a file on disk by streaming chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verifies that the disk file matches its authoritative expected SHA-256 hash."""
    if not file_path.exists():
        logger.error("Exhibit file does not exist for integrity check: %s", file_path)
        return False
    actual_hash = compute_file_sha256(file_path)
    is_match = secrets.compare_digest(actual_hash.lower(), expected_hash.lower())
    if not is_match:
        logger.critical(
            "TAMPERING_ALARM: SHA-256 mismatch detected on exhibit %s! Expected=%s Actual=%s",
            file_path.name,
            expected_hash,
            actual_hash,
        )
    return is_match
