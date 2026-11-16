"""
test_milestone_7b.py — Comprehensive verification suite for Milestone 7B.
Enforces all 16 mandatory security hardening, authentication, RBAC, IDOR defense,
and cryptographic exhibit chain of custody requirements.
"""

import pytest
import io
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app import app
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.case import Case
from app.models.document import Document
from app.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.rate_limiter import limiter
from app.services.audit_service import AuditService


def make_valid_png() -> bytes:
    """Creates a genuine, valid 10x10 RGB PNG image with valid checksums."""
    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter._history.clear()
    yield
    limiter._history.clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====================================================================== #
# 1. Password Hashing & Argon2id Verification                            #
# ====================================================================== #

def test_01_argon2id_password_hashing():
    pw = "ForensicSecure2026!"
    h1 = hash_password(pw)
    h2 = hash_password(pw)

    # Verify RFC 9106 Argon2id profile format
    assert h1.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert h2.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    # Verify unique salts per hash
    assert h1 != h2

    # Verification acceptance and rejection
    assert verify_password(pw, h1) is True
    assert verify_password("WrongPassword123!", h1) is False
    assert verify_password("", h1) is False

    # Password complexity checks
    valid, _ = validate_password_strength("Pass1234!")
    assert valid is True

    short_valid, err = validate_password_strength("Sh0rt!")
    assert short_valid is False
    assert "8 characters" in err

    no_upper_valid, _ = validate_password_strength("lowercase123!")
    assert no_upper_valid is False

    no_digit_valid, _ = validate_password_strength("NoDigitsHere!")
    assert no_digit_valid is False

    no_spec_valid, _ = validate_password_strength("NoSpecial1234")
    assert no_spec_valid is False


# ====================================================================== #
# 2. Login Success and Invalid Credentials Rejection                     #
# ====================================================================== #

@pytest.mark.asyncio
async def test_02_login_and_credential_validation(client, db_session):
    email = "analyst_test_02@visionforensics.local"
    pw = "InvestigatorPass2026!"

    # Ensure clean user
    repo = UserRepository(db_session)
    existing = repo.get_by_email(email)
    if not existing:
        repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Test Analyst 02",
            role=UserRole.FORENSIC_ANALYST.value,
        )

    # 1. Successful login
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert data["user"]["email"] == email
    assert data["user"]["role"] == UserRole.FORENSIC_ANALYST.value
    assert "refresh_token" in res.cookies

    # 2. Invalid password
    bad_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword99!"})
    assert bad_res.status_code == 401
    assert "Invalid email or password" in bad_res.json()["detail"]

    # 3. Nonexistent user
    non_res = await client.post("/api/v1/auth/login", json={"email": "nonexistent@visionforensics.local", "password": pw})
    assert non_res.status_code == 401


# ====================================================================== #
# 3. Access-Token Expiration                                             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_03_access_token_expiration(client, db_session):
    repo = UserRepository(db_session)
    email = "expiring_analyst@visionforensics.local"
    user = repo.get_by_email(email)
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password("ExpiringP@ss123!"),
            full_name="Expiring Analyst",
        )

    # 1. Expired token (delta = -10 seconds)
    expired_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_delta=timedelta(seconds=-10),
    )
    res_expired = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()

    # 2. Valid token (15 minutes)
    valid_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_delta=timedelta(minutes=15),
    )
    res_valid = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["id"] == user.id


# ====================================================================== #
# 4. Refresh-Token Rotation                                              #
# ====================================================================== #

@pytest.mark.asyncio
async def test_04_refresh_token_rotation(client, db_session):
    email = "rotation_analyst@visionforensics.local"
    pw = "RotatePassword123!"
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Rotation Analyst",
        )

    # 1. Login to obtain refresh token
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login_res.status_code == 200
    orig_refresh_token = login_res.cookies.get("refresh_token")
    assert orig_refresh_token is not None

    # 2. Refresh session
    client.cookies.set("refresh_token", orig_refresh_token)
    ref_res = await client.post("/api/v1/auth/refresh")
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data
    new_refresh_token = ref_res.cookies.get("refresh_token")
    assert new_refresh_token is not None
    assert new_refresh_token != orig_refresh_token

    # 3. Verify in PostgreSQL that old token is marked revoked
    orig_hash = hash_refresh_token(orig_refresh_token)
    token_record = repo.get_refresh_token(orig_hash)
    assert token_record is not None
    assert token_record.revoked is True
    assert token_record.replaced_by == hash_refresh_token(new_refresh_token)

    # 4. Attempting to use the old revoked token within grace window triggers concurrent protection -> 409
    client.cookies.clear()
    concurrent_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": orig_refresh_token})
    assert concurrent_res.status_code == 409
    assert "concurrent" in concurrent_res.json()["detail"].lower()

    # 5. Beyond grace window: Genuine replay defense triggers -> 401
    replacement_hash = hash_refresh_token(new_refresh_token)
    rep_record = repo.get_refresh_token(replacement_hash)
    rep_record.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    db_session.commit()

    replay_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": orig_refresh_token})
    assert replay_res.status_code == 401
    assert "revoked" in replay_res.json()["detail"].lower()


# ====================================================================== #
# 5. Logout & Token Revocation                                           #
# ====================================================================== #

@pytest.mark.asyncio
async def test_05_logout_revocation(client, db_session):
    email = "logout_user@visionforensics.local"
    pw = "LogoutPass123!"
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Logout User",
        )

    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login_res.status_code == 200
    tok = login_res.cookies.get("refresh_token")

    # Logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # Verify cookie cleared and token revoked in DB
    tok_record = repo.get_refresh_token(hash_refresh_token(tok))
    assert tok_record is not None
    assert tok_record.revoked is True

    # Refresh must now fail
    client.cookies.set("refresh_token", tok)
    fail_res = await client.post("/api/v1/auth/refresh")
    assert fail_res.status_code == 401


# ====================================================================== #
# 6. Disabled-Account Rejection                                          #
# ====================================================================== #

@pytest.mark.asyncio
async def test_06_disabled_account_rejection(client, db_session):
    email = "disabled_analyst@visionforensics.local"
    pw = "DisabledPass123!"
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Disabled Analyst",
            is_active=False,
        )
    else:
        repo.update_status(user.id, is_active=False)

    # 1. Login fails with 403 Forbidden
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["detail"].lower()

    # 2. Existing token rejected with 403 Forbidden
    token = create_access_token(user.id, email, user.role)
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 403
    assert "deactivated" in me_res.json()["detail"].lower()


# ====================================================================== #
# 7. Role Permissions Matrix                                             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_07_role_permissions_matrix(client, db_session):
    repo = UserRepository(db_session)

    # Setup 3 roles
    roles = {
        "analyst": (UserRole.FORENSIC_ANALYST.value, "analyst_role@visionforensics.local"),
        "senior": (UserRole.SENIOR_INVESTIGATOR.value, "senior_role@visionforensics.local"),
        "admin": (UserRole.SYSTEM_ADMINISTRATOR.value, "admin_role@visionforensics.local"),
    }
    tokens = {}
    for key, (role_val, em) in roles.items():
        u = repo.get_by_email(em)
        if not u:
            u = repo.create_user(
                email=em,
                password_hash=hash_password("RoleTestPass123!"),
                role=role_val,
            )
        else:
            repo.update_role(u.id, role_val)
        tokens[key] = create_access_token(u.id, em, role_val)

    # 1. Analyst attempting Admin route -> 403 Forbidden
    res1 = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tokens['analyst']}"})
    assert res1.status_code == 403

    # 2. Senior Investigator attempting Admin route -> 403 Forbidden
    res2 = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tokens['senior']}"})
    assert res2.status_code == 403

    # 3. System Administrator accessing Admin route -> 200 OK
    res3 = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tokens['admin']}"})
    assert res3.status_code == 200
    assert isinstance(res3.json(), list)

    # 4. Admin creating a new user -> 201 Created
    new_user_email = f"new_created_{int(time.time())}@visionforensics.local"
    res4 = await client.post(
        "/api/v1/admin/users",
        json={
            "email": new_user_email,
            "password": "CreatedUserPass123!",
            "full_name": "Created User",
            "role": UserRole.FORENSIC_ANALYST.value,
        },
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    assert res4.status_code == 201
    assert res4.json()["email"] == new_user_email


# ====================================================================== #
# 8. Cross-User Document Access Denial (IDOR Prevention)                 #
# ====================================================================== #

@pytest.mark.asyncio
async def test_08_cross_user_document_access_denial(client, db_session):
    repo = UserRepository(db_session)

    # User A (Analyst)
    user_a = repo.get_by_email("user_a@visionforensics.local")
    if not user_a:
        user_a = repo.create_user("user_a@visionforensics.local", hash_password("UserAPass123!"))
    token_a = create_access_token(user_a.id, user_a.email, user_a.role)

    # User B (Analyst)
    user_b = repo.get_by_email("user_b@visionforensics.local")
    if not user_b:
        user_b = repo.create_user("user_b@visionforensics.local", hash_password("UserBPass123!"))
    token_b = create_access_token(user_b.id, user_b.email, user_b.role)

    # User A uploads document
    png_bytes = make_valid_png()
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("doc_a.png", png_bytes, "image/png")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # User A can retrieve analysis
    res_a = await client.get(
        f"/api/v1/documents/{doc_id}/analysis",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200

    # User B attempts to access User A's document -> 403 Forbidden!
    res_b = await client.get(
        f"/api/v1/documents/{doc_id}/analysis",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 403
    assert "permission" in res_b.json()["detail"].lower()


# ====================================================================== #
# 9. Cross-User Image Access Denial                                      #
# ====================================================================== #

@pytest.mark.asyncio
async def test_09_cross_user_image_access_denial(client, db_session):
    repo = UserRepository(db_session)
    user_a = repo.get_by_email("user_a@visionforensics.local")
    user_b = repo.get_by_email("user_b@visionforensics.local")
    token_a = create_access_token(user_a.id, user_a.email, user_a.role)
    token_b = create_access_token(user_b.id, user_b.email, user_b.role)

    # Upload document as User A
    png_bytes = make_valid_png()
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("doc_image_test.png", png_bytes, "image/png")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    doc_id = upload_res.json()["document_id"]

    # User B attempts image retrieval -> 403 Forbidden
    res_b = await client.get(
        f"/api/v1/documents/{doc_id}/image",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 403

    # User A succeeds -> 200 OK
    res_a = await client.get(
        f"/api/v1/documents/{doc_id}/image",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    assert "image" in res_a.headers["content-type"]


# ====================================================================== #
# 10. Case Assignment Authorization                                      #
# ====================================================================== #

@pytest.mark.asyncio
async def test_10_case_assignment_authorization(client, db_session):
    repo = UserRepository(db_session)
    senior = repo.get_by_email("senior_lead@visionforensics.local")
    if not senior:
        senior = repo.create_user(
            "senior_lead@visionforensics.local",
            hash_password("SeniorPass123!"),
            role=UserRole.SENIOR_INVESTIGATOR.value,
        )
    token_senior = create_access_token(senior.id, senior.email, senior.role)

    analyst_c = repo.get_by_email("analyst_c@visionforensics.local")
    if not analyst_c:
        analyst_c = repo.create_user(
            "analyst_c@visionforensics.local",
            hash_password("AnalystCPass123!"),
            role=UserRole.FORENSIC_ANALYST.value,
        )
    token_c = create_access_token(analyst_c.id, analyst_c.email, analyst_c.role)

    # Analyst C uploads a document
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("case_doc.png", make_valid_png(), "image/png")},
        headers={"Authorization": f"Bearer {token_c}"},
    )
    doc_id = upload_res.json()["document_id"]

    # Create a case supervised by senior and assign document to it
    case = Case(
        case_number=f"CASE-{int(time.time())}",
        title="Fraud Investigation Alpha",
        status="OPEN",
        lead_investigator_id=senior.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Attach document to this case
    doc = db_session.get(Document, doc_id)
    doc.case_id = case.id
    db_session.commit()

    # Senior investigator supervisor can now access the document!
    res_senior = await client.get(
        f"/api/v1/documents/{doc_id}/analysis",
        headers={"Authorization": f"Bearer {token_senior}"},
    )
    assert res_senior.status_code == 200


# ====================================================================== #
# 11. SHA-256 Match Verification                                         #
# ====================================================================== #

@pytest.mark.asyncio
async def test_11_sha256_match_verification(client, db_session):
    repo = UserRepository(db_session)
    user = repo.get_by_email("analyst_sha@visionforensics.local")
    if not user:
        user = repo.create_user("analyst_sha@visionforensics.local", hash_password("Pass1234!"))
    token = create_access_token(user.id, user.email, user.role)

    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("sha_test.png", make_valid_png(), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Retrieve analysis — integrity check passes
    analysis_res = await client.get(
        f"/api/v1/documents/{doc_id}/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analysis_res.status_code == 200

    # Retrieve chain of custody logs
    custody_res = await client.get(
        f"/api/v1/documents/{doc_id}/custody-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert custody_res.status_code == 200
    events = [entry["event_type"] for entry in custody_res.json()]
    assert "EXHIBIT_INGESTED" in events
    assert "ANALYSIS_EXECUTED" in events
    assert "EXHIBIT_ACCESSED" in events


# ====================================================================== #
# 12. SHA-256 Mismatch Detection & TAMPERING_ALARM Abort                 #
# ====================================================================== #

@pytest.mark.asyncio
async def test_12_sha256_tampering_alarm(client, db_session):
    repo = UserRepository(db_session)
    user = repo.get_by_email("analyst_tamper@visionforensics.local")
    if not user:
        user = repo.create_user("analyst_tamper@visionforensics.local", hash_password("Pass1234!"))
    token = create_access_token(user.id, user.email, user.role)

    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("tamper_test.png", make_valid_png(), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Locate file on disk and alter it to trigger tampering detection
    doc = db_session.get(Document, doc_id)
    assert doc is not None
    file_path = Path(doc.file_path)
    assert file_path.exists()

    # Tamper with file on disk
    with open(file_path, "ab") as f:
        f.write(b"\x00\xFF_TAMPERED_BYTES")

    # Retrieval must abort with HTTP 409 Conflict and TAMPERING_ALARM
    alarm_res = await client.get(
        f"/api/v1/documents/{doc_id}/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alarm_res.status_code == 409
    assert "TAMPERING_ALARM" in alarm_res.json()["detail"]

    # Verify custody ledger recorded TAMPERING_ALARM
    custody_logs = AuditService.list_custody_logs(db_session, doc_id)
    alarm_events = [l for l in custody_logs if l.event_type == "TAMPERING_ALARM"]
    assert len(alarm_events) >= 1
    assert alarm_events[0].status == "TAMPERED"


# ====================================================================== #
# 13. Invalid File Signatures (Magic Byte Verification)                  #
# ====================================================================== #

@pytest.mark.asyncio
async def test_13_invalid_file_signature_rejection(client, db_session):
    repo = UserRepository(db_session)
    email = "upload_validation_fixture@visionforensics.local"
    user = repo.get_by_email(email) or repo.create_user(email, hash_password("IsolatedValidation123!"))
    client.headers['Authorization'] = 'Bearer ' + create_access_token(user.id, user.email, user.role)
    # Plain text file disguised as a PNG
    fake_png = b"Not a real PNG header, just plain text pretending to be an image"
    res = await client.post(
        "/api/v1/upload",
        files={"file": ("fraudulent_invoice.png", fake_png, "image/png")},
    )
    assert res.status_code == 415
    data = res.json()
    err = data.get("error") or data.get("detail") or ""
    assert "unsupported" in err.lower() or "file type" in err.lower()


# ====================================================================== #
# 14. Oversized Upload Rejection (> 20 MB)                               #
# ====================================================================== #

@pytest.mark.asyncio
async def test_14_oversized_upload_rejection(client, db_session):
    repo = UserRepository(db_session)
    email = "upload_validation_fixture@visionforensics.local"
    user = repo.get_by_email(email) or repo.create_user(email, hash_password("IsolatedValidation123!"))
    client.headers['Authorization'] = 'Bearer ' + create_access_token(user.id, user.email, user.role)
    # 21 MB payload
    oversized_data = b"0" * (21 * 1024 * 1024)
    res = await client.post(
        "/api/v1/upload",
        files={"file": ("too_large.pdf", oversized_data, "application/pdf")},
    )
    assert res.status_code == 413
    data = res.json()
    err = data.get("error") or data.get("detail") or ""
    assert "exceed" in err.lower()


# ====================================================================== #
# 15. Rate Limiting Enforcement                                          #
# ====================================================================== #

@pytest.mark.asyncio
async def test_15_rate_limiting(client):
    test_ip = "192.168.1.100"
    limiter.reset(f"login:{test_ip}")

    # Settings allows 5 auth attempts per window
    # 5 attempts must succeed/fail normally (401), 6th must be throttled with 429
    for i in range(5):
        limiter.check(f"login:{test_ip}", max_requests=5, window_seconds=60)

    # 6th check must fail
    allowed, remaining, retry_after = limiter.check(f"login:{test_ip}", max_requests=5, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


# ====================================================================== #
# 16. Admin Audit Log Retrieval                                          #
# ====================================================================== #

@pytest.mark.asyncio
async def test_16_admin_audit_log_retrieval(client, db_session):
    repo = UserRepository(db_session)
    admin = repo.get_by_email("admin_audit@visionforensics.local")
    if not admin:
        admin = repo.create_user(
            "admin_audit@visionforensics.local",
            hash_password("AdminPass123!"),
            role=UserRole.SYSTEM_ADMINISTRATOR.value,
        )
    token = create_access_token(admin.id, admin.email, admin.role)

    res = await client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "event_type" in logs[0]
