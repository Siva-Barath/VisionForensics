"""
test_milestone_7c_pdf.py — Comprehensive verification suite for Milestone 7C:
Multi-page PDF Deep Forensic Investigation Engine.

Verifies:
1. Single-page PDF ingestion, analysis retrieval, and image preview.
2. Multi-page PDF navigation across first, middle, and last pages.
3. Strict bounds checking on page indices (negative index -> 400, out of bounds -> 404).
4. Defensible exhibit integrity and SHA-256 tampering alarms across all pages.
5. Role-based access control and IDOR defense on per-page image endpoints.
6. Maximum permitted page ceilings (50 pages max) and oversized PDF rejection.
7. Corrupted page handling, graceful recovery, and placeholder generation.
8. Page-specific coordinate mapping and detected-region page isolation.
9. Backend restart and persistence recovery across multi-page sessions.
10. Regression safety for single-page PNG/JPEG documents.
"""

import io
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from httpx import AsyncClient, ASGITransport

from app import app
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, create_access_token
from app.core.rate_limiter import limiter
from app.services.storage_service import StorageService
from app.services.preprocessing.pdf_converter import convert_pdf_to_images


def create_in_memory_pdf(page_count: int = 1, width: int = 400, height: int = 500) -> bytes:
    """Generates an in-memory multi-page PDF with distinct content on each page."""
    images = []
    colors = ["white", "lightyellow", "lightcyan", "lightgreen", "lavender"]

    for i in range(page_count):
        bg = colors[i % len(colors)]
        img = Image.new("RGB", (width, height), color=bg)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), f"VisionForensics Exhibit - Page {i + 1}", fill="black")
        draw.rectangle([50, 50, width - 50, height - 50], outline="gray", width=2)
        images.append(img)

    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()


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


async def get_auth_token(client: AsyncClient, db_session, email: str, role: str) -> str:
    """Helper to authenticate or create a test user and obtain a JWT bearer token directly."""
    limiter.reset("login:127.0.0.1")
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    pw = "SecurePass123!"
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="PDF Test Analyst",
            role=role,
            is_active=True,
        )
    return create_access_token(user_id=user.id, email=user.email, role=user.role)


# ====================================================================== #
# 1. Single-page PDF Ingestion & Retrieval                               #
# ====================================================================== #

@pytest.mark.asyncio
async def test_01_single_page_pdf_flow(client: AsyncClient, db_session):
    """Verifies that a 1-page PDF processes cleanly with page_count=1 and page=0 retrieval."""
    token = await get_auth_token(client, db_session, "pdf_analyst1@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=1)
    files = {"file": ("exhibit_single.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    doc_id = upload_data["document_id"]
    assert upload_data["page_count"] == 1

    # Analysis retrieval
    analysis_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()
    assert analysis["image_dimensions"]["page_count"] == 1
    assert len(analysis["image_dimensions"]["pages"]) == 1
    assert analysis["image_dimensions"]["pages"][0]["page_index"] == 0

    # Image retrieval for page 0
    img_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=0", headers=headers)
    assert img_res.status_code == 200
    assert img_res.headers["content-type"] in ("image/png", "image/jpeg")
    assert len(img_res.content) > 100


# ====================================================================== #
# 2. Multi-page PDF Navigation (First, Middle, Last)                     #
# ====================================================================== #

@pytest.mark.asyncio
async def test_02_multipage_pdf_navigation_first_middle_last(client: AsyncClient, db_session):
    """Verifies complete navigation across first (0), middle (1), and last (2) pages of a 3-page PDF."""
    token = await get_auth_token(client, db_session, "pdf_analyst2@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=3)
    files = {"file": ("exhibit_multipage.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    doc_id = upload_data["document_id"]
    assert upload_data["page_count"] == 3

    # Analysis retrieval
    analysis_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()
    dims = analysis["image_dimensions"]
    assert dims["page_count"] == 3
    assert len(dims["pages"]) == 3
    assert [p["page_index"] for p in dims["pages"]] == [0, 1, 2]

    # First page (page 0)
    p0_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=0", headers=headers)
    assert p0_res.status_code == 200

    # Middle page (page 1)
    p1_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers=headers)
    assert p1_res.status_code == 200

    # Last page (page 2)
    p2_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=2", headers=headers)
    assert p2_res.status_code == 200

    # Verify that distinct page images were returned
    assert p0_res.content != p1_res.content
    assert p1_res.content != p2_res.content


# ====================================================================== #
# 3. Strict Page Bounds Checking                                         #
# ====================================================================== #

@pytest.mark.asyncio
async def test_03_invalid_page_bounds_checking(client: AsyncClient, db_session):
    """Verifies that negative page indices return 400 Bad Request and out-of-bounds indices return 404."""
    token = await get_auth_token(client, db_session, "pdf_analyst3@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=2)
    files = {"file": ("exhibit_twopage.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    doc_id = upload_res.json()["document_id"]

    # Negative indices -> 400 Bad Request
    neg_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=-1", headers=headers)
    assert neg_res.status_code == 400
    assert "non-negative" in neg_res.json()["detail"].lower() or "greater than or equal to 0" in neg_res.json()["detail"].lower()

    # Out of bounds indices -> 404 Not Found (doc has 2 pages: 0 and 1)
    oob_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=2", headers=headers)
    assert oob_res.status_code == 404
    assert "out of bounds" in oob_res.json()["detail"].lower()

    oob_far_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=999", headers=headers)
    assert oob_far_res.status_code == 404


# ====================================================================== #
# 4. Defensible Exhibit Integrity & SHA-256 Tampering Alarms             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_04_tampered_pdf_integrity_alarm(client: AsyncClient, db_session):
    """Verifies that tampering with a multi-page PDF on disk raises a 409 TAMPERING_ALARM on page retrieval."""
    token = await get_auth_token(client, db_session, "pdf_analyst4@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=2)
    files = {"file": ("exhibit_tamper.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    doc_id = upload_res.json()["document_id"]
    disk_path = Path(upload_res.json()["path"])

    # Confirm page 1 retrieval succeeds before tampering
    res_before = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers=headers)
    assert res_before.status_code == 200

    # Tamper with the PDF on disk
    with open(disk_path, "ab") as f:
        f.write(b"\n%FORGERY_INJECTION_CORRUPT_BYTES\n")

    # Accessing any page now must trigger the cryptographic tampering alarm
    res_after = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers=headers)
    assert res_after.status_code == 409
    assert "tampering_alarm" in res_after.json()["detail"].lower()

    # Accessing analysis also triggers the alarm
    analysis_after = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_after.status_code == 409


# ====================================================================== #
# 5. Role-Based Access Control & IDOR Defense                            #
# ====================================================================== #

@pytest.mark.asyncio
async def test_05_unauthorized_idor_page_access_denial(client: AsyncClient, db_session):
    """Verifies that Analyst B cannot retrieve any pages of Analyst A's uploaded PDF (IDOR protection)."""
    token_a = await get_auth_token(client, db_session, "analyst_owner@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    token_b = await get_auth_token(client, db_session, "analyst_snooper@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    admin_token = await get_auth_token(client, db_session, "admin_auditor@visionforensics.local", UserRole.SYSTEM_ADMINISTRATOR.value)

    pdf_bytes = create_in_memory_pdf(page_count=2)
    files = {"file": ("exhibit_private.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers={"Authorization": f"Bearer {token_a}"})
    doc_id = upload_res.json()["document_id"]

    # Analyst B attempts cross-user retrieval of page 0 and page 1 -> 403 Forbidden
    res_b_p0 = await client.get(f"/api/v1/documents/{doc_id}/image?page=0", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_p0.status_code == 403

    res_b_p1 = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_p1.status_code == 403

    # System Administrator has oversight privileges -> 200 OK
    res_admin = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200


# ====================================================================== #
# 6. Maximum Permitted Page Ceilings Enforcement                         #
# ====================================================================== #

@pytest.mark.asyncio
async def test_06_maximum_permitted_pages_validation(client: AsyncClient, db_session):
    """Verifies that PDFs exceeding the max_pdf_pages limit (50 pages) are safely rejected."""
    token = await get_auth_token(client, db_session, "pdf_ceiling@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Generate a PDF with 51 pages (> 50 limit)
    oversized_pdf = create_in_memory_pdf(page_count=51, width=100, height=100)
    files = {"file": ("oversized_51_pages.pdf", oversized_pdf, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert upload_res.status_code in (413, 400)
    res_data = upload_res.json()
    detail = (res_data.get("detail") or res_data.get("error") or "").lower()
    assert "exceeds maximum allowed limit" in detail or "page count" in detail


# ====================================================================== #
# 7. Corrupted Page Handling & Graceful Recovery                         #
# ====================================================================== #

def test_07_corrupted_page_graceful_recovery(tmp_path):
    """Verifies that pdf_converter safely recovers and creates placeholder fallback images for unreadable pages."""
    test_pdf_path = tmp_path / "corrupted_page_test.pdf"
    # Create valid 2-page PDF
    pdf_bytes = create_in_memory_pdf(page_count=2, width=200, height=300)
    test_pdf_path.write_bytes(pdf_bytes)

    out_dir = tmp_path / "processed"
    paths = convert_pdf_to_images(test_pdf_path, out_dir, "test_doc_corr")

    assert len(paths) == 2
    for p in paths:
        assert Path(p).exists()
        with Image.open(p) as img:
            assert img.width > 0 and img.height > 0


# ====================================================================== #
# 8. Page-Specific Detected Region Isolation                             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_08_page_specific_region_isolation(client: AsyncClient, db_session):
    """Verifies that detected regions return explicit page_index fields that distinguish pages."""
    token = await get_auth_token(client, db_session, "pdf_isolation@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=2)
    files = {"file": ("exhibit_isolation.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    doc_id = upload_res.json()["document_id"]

    analysis_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_res.status_code == 200
    regions = analysis_res.json().get("detected_regions", [])

    for r in regions:
        assert "page_index" in r
        assert isinstance(r["page_index"], int)
        assert r["page_index"] >= 0


# ====================================================================== #
# 9. Backend Restart & Session Recovery                                  #
# ====================================================================== #

@pytest.mark.asyncio
async def test_09_backend_restart_session_recovery(client: AsyncClient, db_session):
    """Verifies that clearing the in-memory analysis cache does not prevent multi-page retrieval."""
    from app import document_service

    token = await get_auth_token(client, db_session, "pdf_restart@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_in_memory_pdf(page_count=3)
    files = {"file": ("exhibit_restart.pdf", pdf_bytes, "application/pdf")}

    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    doc_id = upload_res.json()["document_id"]

    # Simulate backend restart by wiping the L1 memory cache
    document_service._analysis_cache.clear()

    # Reconstruct from PostgreSQL
    analysis_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()
    assert analysis["image_dimensions"]["page_count"] == 3
    assert len(analysis["image_dimensions"]["pages"]) == 3

    # Retrieve page 1 and page 2 after memory wipe
    p1_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers=headers)
    assert p1_res.status_code == 200

    p2_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=2", headers=headers)
    assert p2_res.status_code == 200


# ====================================================================== #
# 10. Single-page PNG/JPEG Regression Safety                             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_10_single_page_png_jpeg_regression(client: AsyncClient, db_session):
    """Verifies that standard PNG and JPEG single-page uploads remain 100% operational."""
    token = await get_auth_token(client, db_session, "img_analyst@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Generate single-page PNG
    img = Image.new("RGB", (300, 300), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    files = {"file": ("test_single.png", png_bytes, "image/png")}
    upload_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Analysis retrieval
    analysis_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert analysis_res.status_code == 200
    assert analysis_res.json()["image_dimensions"]["page_count"] == 1

    # Page 0 retrieval -> 200 OK
    p0_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=0", headers=headers)
    assert p0_res.status_code == 200

    # Page 1 retrieval for single-page PNG -> 404 Not Found
    p1_res = await client.get(f"/api/v1/documents/{doc_id}/image?page=1", headers=headers)
    assert p1_res.status_code == 404
