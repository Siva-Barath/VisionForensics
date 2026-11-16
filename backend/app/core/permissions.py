"""
permissions.py — Explicit Role-Based Access Control (RBAC) definitions.
Enforces permissions across Forensic Analyst, Senior Investigator, and System Administrator roles.
"""

from __future__ import annotations
from enum import Enum
from typing import Set, Dict
from app.models.user import UserRole


class Permission(str, Enum):
    # Document Exhibits
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_VIEW_OWN = "document:view_own"
    DOCUMENT_VIEW_ASSIGNED = "document:view_assigned"
    DOCUMENT_VIEW_ALL = "document:view_all"
    DOCUMENT_DELETE = "document:delete"

    # Reports
    REPORT_GENERATE_DRAFT = "report:generate_draft"
    REPORT_APPROVE = "report:approve"
    REPORT_EXPORT_CERTIFIED = "report:export_certified"

    # Case Management
    CASE_VIEW_ASSIGNED = "case:view_assigned"
    CASE_VIEW_ALL = "case:view_all"
    CASE_STATUS_MANAGE = "case:status_manage"

    # Administration & Auditing
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG_MANAGE = "system:config_manage"
    SECURITY_AUDIT_VIEW = "security:audit_view"


# Role-to-Permissions Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.FORENSIC_ANALYST: {
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_VIEW_OWN,
        Permission.DOCUMENT_VIEW_ASSIGNED,
        Permission.REPORT_GENERATE_DRAFT,
        Permission.CASE_VIEW_ASSIGNED,
    },
    UserRole.SENIOR_INVESTIGATOR: {
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_VIEW_OWN,
        Permission.DOCUMENT_VIEW_ASSIGNED,
        Permission.REPORT_GENERATE_DRAFT,
        Permission.REPORT_APPROVE,
        Permission.REPORT_EXPORT_CERTIFIED,
        Permission.CASE_VIEW_ASSIGNED,
        Permission.CASE_VIEW_ALL,
        Permission.CASE_STATUS_MANAGE,
    },
    UserRole.SYSTEM_ADMINISTRATOR: {
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_VIEW_OWN,
        Permission.DOCUMENT_VIEW_ASSIGNED,
        Permission.DOCUMENT_VIEW_ALL,
        Permission.DOCUMENT_DELETE,
        Permission.REPORT_GENERATE_DRAFT,
        Permission.REPORT_APPROVE,
        Permission.REPORT_EXPORT_CERTIFIED,
        Permission.CASE_VIEW_ASSIGNED,
        Permission.CASE_VIEW_ALL,
        Permission.CASE_STATUS_MANAGE,
        Permission.USER_MANAGE,
        Permission.SYSTEM_CONFIG_MANAGE,
        Permission.SECURITY_AUDIT_VIEW,
    },
}


def has_permission(role_str: str, permission: Permission) -> bool:
    """Checks whether a given role string possesses a required permission."""
    try:
        role = UserRole(role_str)
        return permission in ROLE_PERMISSIONS.get(role, set())
    except ValueError:
        return False
