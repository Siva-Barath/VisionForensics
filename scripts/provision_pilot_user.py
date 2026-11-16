"""
provision_pilot_user.py — Administrative CLI utility for provisioning authorized pilot accounts.
Enforces Argon2id password hashing, password complexity validation, and security audit logging.

Usage:
    python scripts/provision_pilot_user.py --email analyst1@pilot.local --name "Dr. Alice Vance" --role FORENSIC_ANALYST
"""

import sys
import argparse
import getpass
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.security import hash_password, validate_password_strength


def parse_args():
    parser = argparse.ArgumentParser(description="Provision an authorized VisionForensics AI pilot user account.")
    parser.add_argument("--email", required=True, help="Institutional email address for the analyst/admin")
    parser.add_argument("--name", required=True, help="Full legal/professional name of the examiner")
    parser.add_argument(
        "--role",
        required=True,
        choices=["FORENSIC_ANALYST", "SENIOR_INVESTIGATOR", "SYSTEM_ADMINISTRATOR"],
        help="Access role to assign",
    )
    parser.add_argument("--password", help="Password (if omitted, will prompt securely via terminal)")
    return parser.parse_args()


def main():
    args = parse_args()
    email = args.email.strip().lower()
    full_name = args.name.strip()
    role_str = args.role.strip()

    # Obtain password securely
    password = args.password
    if not password:
        password = getpass.getpass("Enter account password: ")
        confirm_pw = getpass.getpass("Confirm account password: ")
        if password != confirm_pw:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    # Validate password complexity
    is_valid, validation_msg = validate_password_strength(password)
    if not is_valid:
        print(f"[SECURITY REJECTION] Password does not satisfy pilot complexity policy: {validation_msg}")
        sys.exit(1)

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        existing = user_repo.get_by_email(email)
        if existing:
            print(f"[ERROR] User account with email '{email}' already exists (ID: {existing.id}).")
            sys.exit(1)

        # Hash password with Argon2id
        pw_hash = hash_password(password)

        # Persist user
        user = user_repo.create_user(
            email=email,
            password_hash=pw_hash,
            full_name=full_name,
            role=role_str,
            is_active=True,
        )

        # Record security audit event
        AuditService.record_security_event(
            db=db,
            event_type="ACCOUNT_PROVISIONED",
            user_id=user.id,
            user_email=user.email,
            ip_address="127.0.0.1",
            details={
                "action": "pilot_account_provisioned",
                "assigned_role": role_str,
                "provisioned_by": "cli_provision_tool",
            },
        )

        print("=" * 65)
        print("PILOT USER ACCOUNT PROVISIONED SUCCESSFULLY")
        print("=" * 65)
        print(f"User ID:    {user.id}")
        print(f"Full Name:  {user.full_name}")
        print(f"Email:      {user.email}")
        print(f"Role:       {user.role}")
        print(f"Algorithm:  Argon2id (m=65536, t=3, p=4)")
        print(f"Status:     ACTIVE")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    main()
