"""
rate_limiter.py — In-memory sliding window rate limiter for security-sensitive endpoints.
Protects login, authentication refresh, and document upload endpoints from brute force and denial of service.
"""

from __future__ import annotations
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from threading import Lock
from fastapi import HTTPException, status


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self) -> None:
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._account_failures: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Evaluates whether an action is allowed for the given key.

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._history[key]
            # Prune events outside current sliding window
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._history[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, 0, retry_after

            valid_timestamps.append(now)
            remaining = max_requests - len(valid_timestamps)
            return True, remaining, 0

    def enforce(self, key: str, max_requests: int, window_seconds: int) -> None:
        """Enforces rate limit, raising HTTP 429 Too Many Requests on violation."""
        allowed, _, retry_after = self.check(key, max_requests, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Too many requests. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    def reset(self, key: str) -> None:
        """Resets rate limit counter for a given key."""
        with self._lock:
            if key in self._history:
                del self._history[key]

    def check_account_lockout(
        self,
        email: str,
        max_failed: int = 5,
        lockout_seconds: int = 900,
    ) -> Tuple[bool, int]:
        """
        Evaluates whether an account is temporarily locked due to excessive failed attempts.
        Returns:
            (is_locked, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - lockout_seconds
        norm_email = email.strip().lower()

        with self._lock:
            timestamps = self._account_failures[norm_email]
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._account_failures[norm_email] = valid_timestamps

            if len(valid_timestamps) >= max_failed:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + lockout_seconds - now))
                return True, retry_after

            return False, 0

    def record_account_failure(self, email: str) -> None:
        """Records a failed authentication attempt against an account identifier."""
        norm_email = email.strip().lower()
        now = time.time()
        with self._lock:
            self._account_failures[norm_email].append(now)

    def reset_account(self, email: str) -> None:
        """Clears failed login attempt history upon successful authentication."""
        norm_email = email.strip().lower()
        with self._lock:
            if norm_email in self._account_failures:
                del self._account_failures[norm_email]


# Global rate limiter instance
limiter = SlidingWindowRateLimiter()
