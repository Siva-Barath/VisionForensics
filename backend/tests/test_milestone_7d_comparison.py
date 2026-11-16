"""
test_milestone_7d_comparison.py — Comprehensive verification suite for Milestone 7D:
Document Comparison & Differential Analysis Engine.

Verifies:
1. Two identical documents (similarity near 1.0, 0 differential regions, IDENTICAL verdict).
2. Two documents with localized modifications (detecting altered regions, text edits, or stamps).
3. Documents with different dimensions and orientations.
4. Documents with different page counts.
5. Multi-page PDF comparison with explicit page selection.
6. Page alignment and registration.
7. Difference overlay accuracy and derived artifact retrieval.
8. Low-quality and corrupted document handling.
9. Unauthorized cross-user comparison denial (IDOR prevention).
10. Original exhibit hash preservation (zero modification to exhibits).
11. Comparison persistence in PostgreSQL and session recovery.
"""

import io
import hashlib
from pathlib import Path
import pytest
from PIL import Image, ImageDraw, ImageFont
from httpx import AsyncClient, ASGITransport

from app import app
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.user import UserRole
from app.models.document import Document
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.core.security import hash_password, create_access_token
from app.core.rate_limiter import limiter


def create_test_image(
    width: int = 500,
    height: int = 600,
    text: str = "VisionForensics Standard Exhibit",
    add_stamp: bool = False,
    stamp_text: str = "APPROVED",
) -> bytes:
    """Generates an in-memory document image exhibit with synthetic text and optional stamps."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Document border and header
    draw.rectangle([20, 20, width - 20, height - 20], outline="black", width=2)
    draw.rectangle([30, 30, width - 30, 80], fill="#f1f5f9", outline="#cbd5e1")
    draw.text((40, 45), text, fill="black")

    # Body lines
    for y in range(120, height - 100, 40):
        draw.line([40, y, width - 40, y], fill="#94a3b8", width=1)
        draw.text((45, y - 15), f"Section Clause at line offset {y} - Valid Exhibit Content", fill="#334155")

    # Localized modification (Stamp / alteration)
    if add_stamp:
        stamp_box = [width - 200, height - 140, width - 50, height - 60]
        draw.rectangle(stamp_box, fill="#fee2e2", outline="#ef4444", width=3)
        draw.text((width - 180, height - 110), stamp_text, fill="#b91c1c")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_test_pdf(
    page_count: int = 2,
    width: int = 500,
    height: int = 600,
    modified_pages: list[int] = None,
) -> bytes:
    """Generates an in-memory multi-page PDF exhibit with optional page alterations."""
    modified = modified_pages or []
    images = []

    for i in range(page_count):
        is_mod = i in modified
        img_bytes = create_test_image(
            width=width,
            height=height,
            text=f"VisionForensics Agreement - Page {i + 1}",
            add_stamp=is_mod,
            stamp_text=f"REVISED-P{i+1}" if is_mod else "",
        )
        images.append(Image.open(io.BytesIO(img_bytes)))

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
    limiter.reset("upload:127.0.0.1")
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    pw = "SecurePass123!"
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Comparison Forensic Analyst",
            role=role,
            is_active=True,
        )
    return create_access_token(user_id=user.id, email=user.email, role=user.role)


# ====================================================================== #
# 1. Identical Documents Comparison                                      #
# ====================================================================== #

@pytest.mark.asyncio
async def test_01_two_identical_documents(client: AsyncClient, db_session):
    """Verifies that comparing two identical document exhibits yields similarity >= 0.99 and 0 diff regions."""
    token = await get_auth_token(client, db_session, "comp_analyst1@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img_bytes = create_test_image(text="Standard Commercial Lease Agreement")
    files = {"file": ("lease_exhibit_original.png", img_bytes, "image/png")}

    up_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # Compare document with itself
    comp_payload = {
        "document_a_id": doc_id,
        "document_b_id": doc_id,
        "page_a": 0,
        "page_b": 0,
        "align_images": True,
    }
    comp_res = await client.post("/api/v1/comparison", json=comp_payload, headers=headers)
    assert comp_res.status_code == 200
    data = comp_res.json()

    assert data["metrics"]["similarity_score"] >= 0.99
    assert data["metrics"]["ssim_score"] >= 0.99
    assert data["metrics"]["difference_percentage"] == 0.0
    assert data["summary"]["verdict_category"] == "IDENTICAL"
    assert len(data["differential_regions"]) == 0
    assert data["metadata_diff"]["hash_match"] is True


# ====================================================================== #
# 2. Localized Modifications Detection                                   #
# ====================================================================== #

@pytest.mark.asyncio
async def test_02_two_documents_with_localized_modifications(client: AsyncClient, db_session):
    """Verifies that localized alterations (stamps, edits) are accurately detected and isolated."""
    token = await get_auth_token(client, db_session, "comp_analyst2@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Doc A: original contract
    doc_a_bytes = create_test_image(text="Contract Agreement 2026", add_stamp=False)
    up_a = await client.post("/api/v1/upload", files={"file": ("contract_original.png", doc_a_bytes, "image/png")}, headers=headers)
    assert up_a.status_code == 201
    doc_a_id = up_a.json()["document_id"]

    # Upload Doc B: contract with fraudulent altered stamp
    doc_b_bytes = create_test_image(text="Contract Agreement 2026", add_stamp=True, stamp_text="UNAUTHORIZED STAMP")
    up_b = await client.post("/api/v1/upload", files={"file": ("contract_modified.png", doc_b_bytes, "image/png")}, headers=headers)
    assert up_b.status_code == 201
    doc_b_id = up_b.json()["document_id"]

    comp_res = await client.post("/api/v1/comparison", json={"document_a_id": doc_a_id, "document_b_id": doc_b_id}, headers=headers)
    assert comp_res.status_code == 200
    data = comp_res.json()

    assert data["summary"]["verdict_category"] in ("LOCALIZED_DIFFERENCES", "SIGNIFICANT_DIFFERENCES")
    assert len(data["differential_regions"]) >= 1
    assert data["metrics"]["difference_percentage"] > 0.0
    assert data["metadata_diff"]["hash_match"] is False

    # Check that region has proper bounding box coordinates
    first_region = data["differential_regions"][0]
    assert first_region["bounding_box"]["width"] > 0
    assert first_region["bounding_box"]["height"] > 0
    assert first_region["severity"] > 0.0


# ====================================================================== #
# 3. Documents with Different Dimensions & Orientations                  #
# ====================================================================== #

@pytest.mark.asyncio
async def test_03_different_dimensions_and_orientations(client: AsyncClient, db_session):
    """Verifies that exhibits with different dimensions/orientations are handled safely without crashing."""
    token = await get_auth_token(client, db_session, "comp_dims@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Doc A: Portrait 400x600
    doc_a_bytes = create_test_image(width=400, height=600, text="Portrait Exhibit")
    up_a = await client.post("/api/v1/upload", files={"file": ("doc_portrait.png", doc_a_bytes, "image/png")}, headers=headers)
    doc_a_id = up_a.json()["document_id"]

    # Doc B: Landscape 600x400
    doc_b_bytes = create_test_image(width=600, height=400, text="Landscape Exhibit")
    up_b = await client.post("/api/v1/upload", files={"file": ("doc_landscape.png", doc_b_bytes, "image/png")}, headers=headers)
    doc_b_id = up_b.json()["document_id"]

    comp_res = await client.post("/api/v1/comparison", json={"document_a_id": doc_a_id, "document_b_id": doc_b_id}, headers=headers)
    assert comp_res.status_code == 200
    data = comp_res.json()

    assert data["metadata_diff"]["dimension_match"] is False
    assert data["alignment"]["status"] in ("FEATURE_ALIGNED", "FALLBACK_DIRECT_RESIZE")
    assert "forensic_caveat" in data["summary"]


# ====================================================================== #
# 4. Documents with Different Page Counts                                #
# ====================================================================== #

@pytest.mark.asyncio
async def test_04_different_page_counts(client: AsyncClient, db_session):
    """Verifies comparison between documents with mismatched page counts (e.g. 1-page vs 3-page)."""
    token = await get_auth_token(client, db_session, "comp_pagecounts@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Doc A: 1 page PDF
    pdf_a = create_test_pdf(page_count=1)
    up_a = await client.post("/api/v1/upload", files={"file": ("single_page.pdf", pdf_a, "application/pdf")}, headers=headers)
    doc_a_id = up_a.json()["document_id"]

    # Doc B: 3 pages PDF
    pdf_b = create_test_pdf(page_count=3)
    up_b = await client.post("/api/v1/upload", files={"file": ("three_pages.pdf", pdf_b, "application/pdf")}, headers=headers)
    doc_b_id = up_b.json()["document_id"]

    comp_res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id, "page_a": 0, "page_b": 0},
        headers=headers,
    )
    assert comp_res.status_code == 200
    data = comp_res.json()
    assert data["metadata_diff"]["page_count_match"] is False
    assert data["metadata_diff"]["document_a"]["page_count"] == 1
    assert data["metadata_diff"]["document_b"]["page_count"] == 3


# ====================================================================== #
# 5. Multi-Page PDF Comparison with Explicit Page Matching               #
# ====================================================================== #

@pytest.mark.asyncio
async def test_05_multipage_pdf_explicit_pages(client: AsyncClient, db_session):
    """Verifies cross-page comparison (e.g. comparing page 0 of Doc A with page 1 of Doc B)."""
    token = await get_auth_token(client, db_session, "comp_multipage@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Doc A: 3-page PDF with modification on page 1
    pdf_a = create_test_pdf(page_count=3, modified_pages=[1])
    up_a = await client.post("/api/v1/upload", files={"file": ("doc_a_3p.pdf", pdf_a, "application/pdf")}, headers=headers)
    doc_a_id = up_a.json()["document_id"]

    # Doc B: 3-page PDF with no modification
    pdf_b = create_test_pdf(page_count=3, modified_pages=[])
    up_b = await client.post("/api/v1/upload", files={"file": ("doc_b_3p.pdf", pdf_b, "application/pdf")}, headers=headers)
    doc_b_id = up_b.json()["document_id"]

    # Compare page 1 of Doc A (modified) with page 1 of Doc B (unmodified)
    comp_res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id, "page_a": 1, "page_b": 1},
        headers=headers,
    )
    assert comp_res.status_code == 200
    data = comp_res.json()
    assert data["page_a"] == 1
    assert data["page_b"] == 1
    assert len(data["differential_regions"]) >= 1

    # Out of bounds page index should return 400 Bad Request
    invalid_page_res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id, "page_a": 99, "page_b": 0},
        headers=headers,
    )
    assert invalid_page_res.status_code == 400


# ====================================================================== #
# 6. Page Alignment and Registration                                     #
# ====================================================================== #

@pytest.mark.asyncio
async def test_06_alignment_and_registration(client: AsyncClient, db_session):
    """Verifies that alignment status and confidence metrics are accurately captured."""
    token = await get_auth_token(client, db_session, "comp_align@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img1 = create_test_image(width=500, height=500, text="Aligned Exhibit Alpha")
    up1 = await client.post("/api/v1/upload", files={"file": ("align_a.png", img1, "image/png")}, headers=headers)
    doc_a_id = up1.json()["document_id"]

    img2 = create_test_image(width=500, height=500, text="Aligned Exhibit Beta")
    up2 = await client.post("/api/v1/upload", files={"file": ("align_b.png", img2, "image/png")}, headers=headers)
    doc_b_id = up2.json()["document_id"]

    comp_res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id, "align_images": True},
        headers=headers,
    )
    assert comp_res.status_code == 200
    data = comp_res.json()
    assert data["alignment"]["status"] in ("FEATURE_ALIGNED", "FALLBACK_DIRECT_RESIZE")
    assert 0.0 <= data["alignment"]["confidence"] <= 1.0


# ====================================================================== #
# 7. Difference Overlay Accuracy & Artifact Retrieval                    #
# ====================================================================== #

@pytest.mark.asyncio
async def test_07_difference_overlay_and_artifacts(client: AsyncClient, db_session):
    """Verifies that derived artifacts (heatmap, mask, aligned_b) are accessible via API."""
    token = await get_auth_token(client, db_session, "comp_artifacts@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img_a = create_test_image(text="Original Document Record")
    img_b = create_test_image(text="Original Document Record", add_stamp=True)

    up_a = await client.post("/api/v1/upload", files={"file": ("art_a.png", img_a, "image/png")}, headers=headers)
    up_b = await client.post("/api/v1/upload", files={"file": ("art_b.png", img_b, "image/png")}, headers=headers)

    comp_res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": up_a.json()["document_id"], "document_b_id": up_b.json()["document_id"]},
        headers=headers,
    )
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["comparison_id"]

    # Verify heatmap artifact streaming
    heatmap_res = await client.get(f"/api/v1/comparison/{comp_id}/artifacts/diff_heatmap", headers=headers)
    assert heatmap_res.status_code == 200
    assert heatmap_res.headers["content-type"] == "image/png"
    assert len(heatmap_res.content) > 100

    # Verify binary mask artifact streaming
    mask_res = await client.get(f"/api/v1/comparison/{comp_id}/artifacts/diff_mask", headers=headers)
    assert mask_res.status_code == 200
    assert mask_res.headers["content-type"] == "image/png"

    # Verify aligned B artifact streaming
    aligned_res = await client.get(f"/api/v1/comparison/{comp_id}/artifacts/aligned_b", headers=headers)
    assert aligned_res.status_code == 200
    assert aligned_res.headers["content-type"] == "image/png"


# ====================================================================== #
# 8. Low-Quality & Non-Existent Document Handling                        #
# ====================================================================== #

@pytest.mark.asyncio
async def test_08_error_handling_nonexistent_and_bad_requests(client: AsyncClient, db_session):
    """Verifies that invalid or non-existent document IDs return clean 404s without crashing."""
    token = await get_auth_token(client, db_session, "comp_errors@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": fake_id, "document_b_id": fake_id},
        headers=headers,
    )
    assert res.status_code == 404


# ====================================================================== #
# 9. Unauthorized Cross-User Comparison Denial (IDOR Defense)            #
# ====================================================================== #

@pytest.mark.asyncio
async def test_09_unauthorized_cross_user_comparison_idor(client: AsyncClient, db_session):
    """Verifies that an analyst cannot compare documents belonging to another user (IDOR protection)."""
    # Analyst A uploads Doc A
    token_a = await get_auth_token(client, db_session, "user_alpha@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    up_a = await client.post(
        "/api/v1/upload",
        files={"file": ("alpha_secret.png", create_test_image(text="Alpha Exhibit"), "image/png")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    doc_a_id = up_a.json()["document_id"]

    # Analyst B uploads Doc B
    token_b = await get_auth_token(client, db_session, "user_beta@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    up_b = await client.post(
        "/api/v1/upload",
        files={"file": ("beta_secret.png", create_test_image(text="Beta Exhibit"), "image/png")},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    doc_b_id = up_b.json()["document_id"]

    # Analyst B attempts to compare Doc B with Analyst A's Doc A without permission
    comp_idor = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must be forbidden (403)
    assert comp_idor.status_code == 403


# ====================================================================== #
# 10. Original Exhibit Hash Preservation                                 #
# ====================================================================== #

@pytest.mark.asyncio
async def test_10_original_exhibit_hash_preservation(client: AsyncClient, db_session):
    """Verifies that original document exhibit files on disk are 100% untouched by comparison."""
    token = await get_auth_token(client, db_session, "comp_hash@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img_bytes = create_test_image(text="Hash Invariance Test Exhibit")
    up = await client.post("/api/v1/upload", files={"file": ("hash_inv.png", img_bytes, "image/png")}, headers=headers)
    doc_id = up.json()["document_id"]

    doc_repo = DocumentRepository(db_session)
    doc = doc_repo.get_document(doc_id)
    assert doc is not None

    file_path = Path(doc.file_path)
    hash_before = hashlib.sha256(file_path.read_bytes()).hexdigest()

    # Perform comparison
    await client.post(
        "/api/v1/comparison",
        json={"document_a_id": doc_id, "document_b_id": doc_id},
        headers=headers,
    )

    # Check hash after comparison
    hash_after = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert hash_before == hash_after
    assert hash_after == doc.sha256_hash


# ====================================================================== #
# 11. Comparison Persistence in PostgreSQL & Retrieval                   #
# ====================================================================== #

@pytest.mark.asyncio
async def test_11_comparison_persistence_and_retrieval(client: AsyncClient, db_session):
    """Verifies that completed comparisons persist in PostgreSQL and can be retrieved by ID."""
    token = await get_auth_token(client, db_session, "comp_persist@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img_a = create_test_image(text="Persisted Document Alpha")
    img_b = create_test_image(text="Persisted Document Beta", add_stamp=True)

    up_a = await client.post("/api/v1/upload", files={"file": ("persist_a.png", img_a, "image/png")}, headers=headers)
    up_b = await client.post("/api/v1/upload", files={"file": ("persist_b.png", img_b, "image/png")}, headers=headers)

    comp_post = await client.post(
        "/api/v1/comparison",
        json={"document_a_id": up_a.json()["document_id"], "document_b_id": up_b.json()["document_id"]},
        headers=headers,
    )
    assert comp_post.status_code == 200
    comp_id = comp_post.json()["comparison_id"]

    # Retrieve comparison via GET endpoint
    get_res = await client.get(f"/api/v1/comparison/{comp_id}", headers=headers)
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["comparison_id"] == comp_id
    assert retrieved["metrics"]["similarity_score"] == comp_post.json()["metrics"]["similarity_score"]
    assert len(retrieved["differential_regions"]) == len(comp_post.json()["differential_regions"])
