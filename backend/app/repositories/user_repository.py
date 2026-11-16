"""
user_repository.py — Data access repository for User accounts and hashed Refresh Tokens.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.user import User, UserRole
from app.models.token import RefreshToken
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository handling database operations for user accounts and refresh tokens."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    # User Operations                                                    #
    # ------------------------------------------------------------------ #

    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: str = UserRole.FORENSIC_ANALYST.value,
        is_active: bool = True,
    ) -> User:
        """Creates a new user record with Argon2id password hash."""
        user = User(
            email=email.strip().lower(),
            hashed_password=password_hash,
            full_name=full_name.strip() if full_name else None,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Created user | id=%s email=%s role=%s", user.id, user.email, user.role)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Finds user by UUID primary key."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Finds user by email address (case-insensitive)."""
        stmt = select(User).where(User.email == email.strip().lower())
        return self.db.scalars(stmt).first()

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lists users ordered by creation date."""
        stmt = select(User).order_by(User.created_at.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update_status(self, user_id: str, is_active: bool) -> Optional[User]:
        """Activates or deactivates a user account."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = is_active
            self.db.commit()
            self.db.refresh(user)
            logger.info("Updated user status | id=%s active=%s", user_id, is_active)
        return user

    def update_role(self, user_id: str, new_role: str) -> Optional[User]:
        """Updates user's RBAC role."""
        user = self.get_by_id(user_id)
        if user:
            user.role = new_role
            self.db.commit()
            self.db.refresh(user)
            logger.info("Updated user role | id=%s new_role=%s", user_id, new_role)
        return user

    # ------------------------------------------------------------------ #
    # Refresh Token Operations                                           #
    # ------------------------------------------------------------------ #

    def save_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Stores a hashed refresh token."""
        token_record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(token_record)
        self.db.commit()
        self.db.refresh(token_record)
        return token_record

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Finds a refresh token by its SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.scalars(stmt).first()

    def get_refresh_token_for_update(self, token_hash: str) -> Optional[RefreshToken]:
        """Finds and acquires a row-level lock on a refresh token using SELECT ... FOR UPDATE."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        return self.db.scalars(stmt).first()

    def rotate_refresh_token_atomic(
        self,
        old_token_hash: str,
        new_token_hash: str,
        new_expires_at: datetime,
        grace_window_seconds: int = 15,
    ) -> Tuple[bool, Optional[RefreshToken], Optional[User], str]:
        """
        Atomically validates, locks, revokes, and rotates a refresh token within a single
        database transaction using SELECT ... FOR UPDATE row-level locking.

        Returns:
            (success: bool, new_token_record: Optional[RefreshToken], user: Optional[User], status: str)
            status values:
              - "SUCCESS": Token rotated successfully.
              - "NOT_FOUND": Token hash does not exist.
              - "CONCURRENT_ROTATION_GRACE": Token was already rotated within the grace window
                 by an in-flight concurrent request. Does NOT revoke user sessions and does NOT
                 return replacement credentials to this caller.
              - "REPLAY_BREACH": Token was revoked outside the grace window. Indicates genuine
                 replay attack; all sessions for the user are immediately revoked.
              - "EXPIRED": Token has expired.
              - "USER_INACTIVE": User account is deactivated or missing.
        """
        try:
            # 1. Acquire row-level lock on the presented refresh token
            stored_token = self.get_refresh_token_for_update(old_token_hash)
            if not stored_token:
                return False, None, None, "NOT_FOUND"

            now = datetime.now(timezone.utc)

            # 2. Check if token is already revoked
            if stored_token.revoked:
                # Check for in-flight concurrent rotation collision within grace window
                if stored_token.replaced_by:
                    replacement = self.db.scalars(
                        select(RefreshToken).where(RefreshToken.token_hash == stored_token.replaced_by)
                    ).first()
                    if replacement and replacement.created_at:
                        rep_created = replacement.created_at
                        if rep_created.tzinfo is None:
                            rep_created = rep_created.replace(tzinfo=timezone.utc)
                        time_since_rotation = (now - rep_created).total_seconds()
                        if time_since_rotation <= grace_window_seconds:
                            logger.warning(
                                "Concurrent refresh collision detected for user %s within grace window (%.1fs). Session preserved.",
                                stored_token.user_id,
                                time_since_rotation,
                            )
                            # Concurrent in-flight request: Do NOT revoke user sessions!
                            # Do NOT return replacement token to prevent credential theft.
                            return False, None, None, "CONCURRENT_ROTATION_GRACE"

                # Beyond grace window: Genuine replay attack detected!
                logger.critical(
                    "DEFENSIBLE REPLAY ALARM: Revoked refresh token reused for user %s beyond grace window. Revoking all sessions.",
                    stored_token.user_id,
                )
                self.revoke_all_user_tokens(stored_token.user_id)
                return False, None, None, "REPLAY_BREACH"

            # 3. Check expiration
            exp_at = stored_token.expires_at
            if exp_at.tzinfo is None:
                exp_at = exp_at.replace(tzinfo=timezone.utc)
            if exp_at <= now:
                stored_token.revoked = True
                self.db.commit()
                return False, None, None, "EXPIRED"

            # 4. Check user account status
            user = self.get_by_id(stored_token.user_id)
            if not user or not user.is_active:
                stored_token.revoked = True
                self.db.commit()
                return False, None, None, "USER_INACTIVE"

            # 5. Atomic Rotation in Single Transaction
            stored_token.revoked = True
            stored_token.replaced_by = new_token_hash

            new_record = RefreshToken(
                user_id=user.id,
                token_hash=new_token_hash,
                expires_at=new_expires_at,
                revoked=False,
            )
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)

            logger.info("Atomically rotated refresh token for user %s", user.id)
            return True, new_record, user, "SUCCESS"

        except Exception as exc:
            self.db.rollback()
            logger.error("Transaction rollback during atomic refresh rotation: %s", exc)
            raise

    def revoke_refresh_token(self, token_hash: str, replaced_by: Optional[str] = None) -> bool:
        """Marks a refresh token as revoked, optionally tracking replacement for rotation."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True, replaced_by=replaced_by)
        )
        res = self.db.execute(stmt)
        self.db.commit()
        return res.rowcount > 0

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revokes all active refresh tokens for a user (used on password reset / forced logout)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        res = self.db.execute(stmt)
        self.db.commit()
        logger.info("Revoked %d refresh tokens for user %s", res.rowcount, user_id)
        return res.rowcount
