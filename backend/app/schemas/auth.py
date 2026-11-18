"""
auth.py — Pydantic request and response schemas for Authentication,
Role-Based Access Control (RBAC), and Audit Logging.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password meeting complexity policy")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of analyst/user")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError(f"'{v}' is not a valid email address.")
        return cleaned


class UserCreateAdminRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password meeting complexity policy")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    role: str = Field("FORENSIC_ANALYST", description="RBAC role: FORENSIC_ANALYST, SENIOR_INVESTIGATOR, SYSTEM_ADMINISTRATOR")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError(f"'{v}' is not a valid email address.")
        return cleaned


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User's registered email address")
    password: str = Field(..., description="Plaintext password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError(f"'{v}' is not a valid email address.")
        return cleaned


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(900, description="Token validity in seconds (default 15 minutes)")
    user: UserResponse


class UserStatusUpdateRequest(BaseModel):
    is_active: Optional[bool] = Field(None, description="Account active status")
    role: Optional[str] = Field(None, description="Updated RBAC role")


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    event_type: str
    category: Optional[str] = "SECURITY_AUTH"
    status: Optional[str] = "SUCCESS"
    sha256_hash: Optional[str] = ""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class CustodyLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    event_type: str
    document_id: str
    user_id: Optional[str] = None
    sha256_hash: str
    status: str
    ip_address: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
