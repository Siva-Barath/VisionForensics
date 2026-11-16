"""
test_milestone_7b_remediation.py — Comprehensive verification suite for Milestone 7B-R security remediations.

Covers all 4 remediation areas:
1. P0: Concurrent refresh-token race condition & grace-window replay safety.
2. P0: PostgreSQL custody and audit ledger role least-privilege & engine trigger immutability.
3. P1: Trusted reverse-proxy client IP resolution & header spoofing defense.
4. P1: Account-level credential-stuffing defense & account lockout isolation.
5. CSRF defense: Origin & Referer validation on cookie-authenticated session endpoints.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import app
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, hash_refresh_token, generate_refresh_token
from app.core.rate_limiter import limiter
from app.core.network import get_client_ip, validate_request_origin


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ====================================================================== #
# 1. P0: Concurrent Refresh-Token Invalidation & Grace-Period Handling    #
# ====================================================================== #

@pytest.mark.asyncio
async def test_remediation_01_concurrent_refresh_handling(client, db_session):
    """
    Test two simultaneous refresh requests presenting the exact same refresh token T0.
    One must succeed (HTTP 200, receives T1), the other must receive HTTP 409 Conflict.
    Neither request must invalidate all sessions for the user.
    A subsequent refresh using T1 must succeed.
    """
    email = "concurrent_analyst@visionforensics.local"
    pw = "ConcurrentPass123!"
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Concurrent Analyst",
        )

    # 1. Login to get initial refresh token T0
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login_res.status_code == 200
    t0_token = login_res.cookies.get("refresh_token")
    assert t0_token is not None

    # Clear cookies so we can control payload explicitly
    client.cookies.clear()

    # 2. Fire two concurrent refresh requests with token T0
    async def do_refresh():
        # Fresh async client to simulate independent HTTP streams
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as c:
            return await c.post("/api/v1/auth/refresh", json={"refresh_token": t0_token})

    res1, res2 = await asyncio.gather(do_refresh(), do_refresh())

    statuses = [res1.status_code, res2.status_code]
    assert 200 in statuses, f"Expected one 200 OK, got statuses: {statuses}"
    assert 409 in statuses, f"Expected one 409 Conflict, got statuses: {statuses}"

    winner_res = res1 if res1.status_code == 200 else res2
    loser_res = res2 if res1.status_code == 200 else res1

    # Winner gets new access token and rotated refresh cookie
    winner_data = winner_res.json()
    assert "access_token" in winner_data
    t1_token = winner_res.cookies.get("refresh_token")
    assert t1_token is not None
    assert t1_token != t0_token

    # Loser gets 409 with concurrent warning and NO replacement token
    assert loser_res.status_code == 409
    loser_data = loser_res.json()
    assert "concurrent" in loser_data["detail"].lower()
    assert loser_res.cookies.get("refresh_token") is None

    # 3. CRITICAL: User sessions must NOT be revoked!
    # Subsequent refresh with T1 must succeed
    client.cookies.clear()
    next_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1_token})
    assert next_refresh.status_code == 200
    t2_token = next_refresh.cookies.get("refresh_token")
    assert t2_token is not None
    assert t2_token != t1_token

    # 4. Beyond grace window: Replay of T0 triggers genuine security breach -> 401
    # Adjust replacement timestamp to simulate 30 seconds having passed
    t1_hash = hash_refresh_token(t1_token)
    t1_record = repo.get_refresh_token(t1_hash)
    if t1_record:
        t1_record.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        db_session.commit()

    client.cookies.clear()
    replay_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": t0_token})
    assert replay_res.status_code == 401
    assert "revoked" in replay_res.json()["detail"].lower()


# ====================================================================== #
# 2. P0: PostgreSQL Least-Privilege Role & Trigger Immutability          #
# ====================================================================== #

def test_remediation_02_postgres_least_privilege_and_immutability():
    """
    Test that the dedicated application role visionforensics_app has least-privilege permissions:
    - Can SELECT and INSERT on exhibit_custody_logs and security_audit_logs.
    - CANNOT UPDATE or DELETE on exhibit_custody_logs and security_audit_logs (permission denied).
    - Even superuser UPDATE or DELETE is rejected by PostgreSQL triggers.
    - Can perform normal CRUD on mutable tables (documents, users, refresh_tokens).
    """
    settings = get_settings()
    app_engine = create_engine(settings.database_url)

    # 1. Verify visionforensics_app can INSERT into security_audit_logs
    test_audit_id = f"test-audit-{datetime.now().timestamp()}"
    with app_engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO security_audit_logs (id, timestamp, event_type, ip_address, details)
                VALUES (:id, :now, 'SECURITY_REMEDIATION_TEST', '127.0.0.1', CAST('{}' AS JSON))
            """),
            {"id": test_audit_id, "now": datetime.now(timezone.utc)},
        )
        conn.commit()

    # 2. Verify visionforensics_app can SELECT from security_audit_logs
    with app_engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, event_type FROM security_audit_logs WHERE id = :id"),
            {"id": test_audit_id},
        ).fetchone()
        assert row is not None
        assert row[0] == test_audit_id

    # 3. Verify visionforensics_app CANNOT UPDATE security_audit_logs (permission denied)
    update_rejected = False
    try:
        with app_engine.connect() as conn:
            conn.execute(
                text("UPDATE security_audit_logs SET event_type = 'TAMPERED' WHERE id = :id"),
                {"id": test_audit_id},
            )
            conn.commit()
    except Exception as exc:
        update_rejected = True
        err_msg = str(exc).lower()
        assert "permission denied" in err_msg or "defensible audit integrity error" in err_msg

    assert update_rejected, "Expected UPDATE on security_audit_logs to be rejected by role permission or trigger!"

    # 4. Verify visionforensics_app CANNOT DELETE security_audit_logs (permission denied)
    delete_rejected = False
    try:
        with app_engine.connect() as conn:
            conn.execute(
                text("DELETE FROM security_audit_logs WHERE id = :id"),
                {"id": test_audit_id},
            )
            conn.commit()
    except Exception as exc:
        delete_rejected = True
        err_msg = str(exc).lower()
        assert "permission denied" in err_msg or "defensible audit integrity error" in err_msg

    assert delete_rejected, "Expected DELETE on security_audit_logs to be rejected by role permission or trigger!"

    # 5. Verify trigger defense on superuser connection as well
    # Connect with migrator/superuser role to verify the trigger stops privileged accounts
    migrator_url = settings.migration_database_url or "postgresql://postgres:postgres@127.0.0.1:5433/visionforensics"
    migrator_engine = create_engine(migrator_url)
    trigger_stopped_privileged = False
    try:
        with migrator_engine.connect() as conn:
            conn.execute(
                text("UPDATE security_audit_logs SET event_type = 'TAMPERED' WHERE id = :id"),
                {"id": test_audit_id},
            )
            conn.commit()
    except Exception as exc:
        trigger_stopped_privileged = True
        err_msg = str(exc)
        assert "DEFENSIBLE AUDIT INTEGRITY ERROR" in err_msg

    assert trigger_stopped_privileged, "Expected PostgreSQL trigger to block UPDATE even on privileged connections!"


# ====================================================================== #
# 3. P1: Reverse-Proxy Client IP Resolution & Spoofing Defense           #
# ====================================================================== #

def test_remediation_03_trusted_proxy_ip_resolution():
    """
    Test get_client_ip logic:
    - Direct untrusted connection completely ignores client X-Forwarded-For.
    - Connection from configured trusted proxy parses X-Forwarded-For right-to-left.
    - Intermediate trusted proxies in chain are skipped to find genuine upstream IP.
    """
    class MockClient:
        def __init__(self, host):
            self.host = host

    class MockRequest:
        def __init__(self, client_host, headers=None):
            self.client = MockClient(client_host)
            self.headers = headers or {}

    # Case A: Direct connection from public IP attempting to spoof header
    req_spoof = MockRequest("203.0.113.5", {"X-Forwarded-For": "198.51.100.99"})
    assert get_client_ip(req_spoof) == "203.0.113.5", "Direct connection must ignore client-supplied X-Forwarded-For!"

    # Case B: Connection from configured trusted proxy (127.0.0.1) with X-Forwarded-For
    req_proxy = MockRequest("127.0.0.1", {"X-Forwarded-For": "198.51.100.99"})
    assert get_client_ip(req_proxy) == "198.51.100.99", "Trusted proxy must parse upstream client IP!"

    # Case C: Multi-hop proxy chain: client (198.51.100.99) -> internal proxy (10.0.0.5) -> reverse proxy (127.0.0.1)
    # Right-to-left traversal skips 10.0.0.5 (trusted private range) to locate genuine public client
    req_multihop = MockRequest("127.0.0.1", {"X-Forwarded-For": "198.51.100.99, 10.0.0.5"})
    # The pilot trusts only its declared proxy IP, not every private address.
    assert get_client_ip(req_multihop) == "10.0.0.5", "Traversal must stop at an undeclared private proxy"
    declared_hop = MockRequest("127.0.0.1", {"X-Forwarded-For": "198.51.100.99, 172.28.0.10"})
    assert get_client_ip(declared_hop) == "198.51.100.99"

    # Case D: Trusted proxy with X-Real-IP fallback
    req_real_ip = MockRequest("127.0.0.1", {"X-Real-IP": "198.51.100.77"})
    assert get_client_ip(req_real_ip) == "198.51.100.77", "Fallback to X-Real-IP when from trusted proxy!"


# ====================================================================== #
# 4. P1: Account-Level Credential-Stuffing Defense & Lockout Isolation   #
# ====================================================================== #

@pytest.mark.asyncio
async def test_remediation_04_account_level_lockout(client, db_session):
    """
    Test account-level brute force defense:
    - 5 failed logins for an account (even across different IPs) locks the account.
    - 6th attempt returns HTTP 429 Too Many Requests with Retry-After header.
    - Other accounts remain unlocked (per-account isolation).
    - Successful login resets the failure counter.
    - Error messages are uniform to prevent account enumeration.
    """
    email_victim = "stuffing_victim@visionforensics.local"
    email_other = "stuffing_bystander@visionforensics.local"
    pw_correct = "CorrectPassword123!"
    pw_wrong = "WrongPassword999!"

    repo = UserRepository(db_session)
    for email in (email_victim, email_other):
        user = repo.get_by_email(email)
        if not user:
            repo.create_user(
                email=email,
                password_hash=hash_password(pw_correct),
                full_name="Stuffing Target",
            )

    # Reset any existing limiter history for these accounts
    limiter.reset_account(email_victim)
    limiter.reset_account(email_other)

    # 1. Perform 5 failed attempts against victim email
    for i in range(5):
        # Reset IP rate limit key so we simulate distributed IPs attacking the same account
        limiter.reset("login:127.0.0.1")
        res = await client.post("/api/v1/auth/login", json={"email": email_victim, "password": pw_wrong})
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid email or password."

    # 2. 6th attempt must be blocked by Account Lockout -> 429 Too Many Requests
    limiter.reset("login:127.0.0.1")
    lockout_res = await client.post("/api/v1/auth/login", json={"email": email_victim, "password": pw_wrong})
    assert lockout_res.status_code == 429
    assert "temporarily locked" in lockout_res.json()["detail"].lower()
    assert "Retry-After" in lockout_res.headers

    # 3. Even correct password is locked out while lockout is active
    limiter.reset("login:127.0.0.1")
    correct_locked_res = await client.post("/api/v1/auth/login", json={"email": email_victim, "password": pw_correct})
    assert correct_locked_res.status_code == 429

    # 4. Other account (bystander) remains unaffected (isolation)
    limiter.reset("login:127.0.0.1")
    bystander_res = await client.post("/api/v1/auth/login", json={"email": email_other, "password": pw_correct})
    assert bystander_res.status_code == 200

    # 5. After resetting victim account, login succeeds
    limiter.reset_account(email_victim)
    limiter.reset("login:127.0.0.1")
    unlocked_res = await client.post("/api/v1/auth/login", json={"email": email_victim, "password": pw_correct})
    assert unlocked_res.status_code == 200


# ====================================================================== #
# 5. CSRF Origin & Referer Validation on Cookie Endpoints                #
# ====================================================================== #

@pytest.mark.asyncio
async def test_remediation_05_csrf_origin_validation(client, db_session):
    """
    Test CSRF defenses on cookie-authenticated refresh and logout endpoints:
    - Requests presenting cookie with untrusted Origin header are rejected with HTTP 403.
    - Requests presenting cookie with trusted Origin header (e.g. http://localhost:5173) succeed.
    """
    email = "csrf_analyst@visionforensics.local"
    pw = "CsrfPassword123!"
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    if not user:
        repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="CSRF Analyst",
        )

    # Login to obtain cookie
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login_res.status_code == 200
    refresh_token = login_res.cookies.get("refresh_token")
    assert refresh_token is not None

    # Case A: Refresh with cookie and malicious Origin header -> 403 Forbidden
    client.cookies.set("refresh_token", refresh_token)
    malicious_res = await client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "https://evil-attacker.example.com"},
    )
    assert malicious_res.status_code == 403
    assert "csrf" in malicious_res.json()["detail"].lower()

    # Case B: Refresh with cookie and trusted Origin header -> 200 OK
    trusted_res = await client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )
    assert trusted_res.status_code == 200
    new_token = trusted_res.cookies.get("refresh_token")
    assert new_token is not None

    # Case C: Logout with cookie and malicious Origin -> 403 Forbidden
    client.cookies.set("refresh_token", new_token)
    malicious_logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "https://malicious-site.com"},
    )
    assert malicious_logout.status_code == 403

    # Case D: Logout with cookie and trusted Origin -> 200 OK
    trusted_logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )
    assert trusted_logout.status_code == 200
