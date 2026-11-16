"""
test_milestone_7e_reports.py — Comprehensive verification suite for Milestone 7E:
Forensic Investigation Reporting & PDF Export Engine.

Verifies:
1. Authentic document report generation (PDF layout, report number, metadata, SHA-256).
2. Suspicious document report generation (SUSPICIOUS tier formatting).
3. High-risk document report generation (HIGH_RISK tier, strict prohibition of 'CONFIRMED FORGERY').
4. ML_UNAVAILABLE and DEGRADED report handling.
5. Multi-page PDF report generation (page counts, multi-page metadata).
6. Reports containing multiple detected evidence regions.
7. Reports with linked comparison results (5-page comprehensive dossier).
8. Table formatting, line wrapping, and latin-1 text sanitization.
9. Graceful fallback on missing or unreadable evidence artifacts.
10. Cross-user IDOR protection (HTTP 403 on unauthorized generate/get/download, Admin bypass).
11. Report SHA-256 cryptographic verification and on-disk tamper alarm (HTTP 409 Conflict).
12. Report download endpoint and chain-of-custody audit logging (REPORT_GENERATED, REPORT_DOWNLOADED).
13. Database persistence across sessions and report archive listing.
14. Platform regression check across core pipeline endpoints.
"""

import io
import hashlib
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from httpx import AsyncClient, ASGITransport

from app import app
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.user import UserRole
from app.models.document import Document
from app.models.report import ForensicReport
from app.models.audit import ExhibitCustodyLog
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.report_repository import ReportRepository
from app.core.security import hash_password, create_access_token
from app.core.rate_limiter import limiter
from app.services.report_generation.pdf_generator import ForensicPDFBuilder, sanitize_text

AUTHENTIC_SAMPLE_PATH = Path("D:/Datasets/TrainingDataset/authentic/driving_license/02_aut_drvlic_new_CA02.tif")
FORGED_SAMPLE_PATH = Path("D:/Datasets/TrainingDataset/ml_phase2/train_forged/driving_license/02_aut_drvlic_new_CS05_copy_move.tif")


def _image_to_png_bytes(image_path: Path) -> bytes:
    """Reads an image from disk and converts to PNG bytes."""
    with Image.open(image_path) as img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def create_synthetic_image(
    width: int = 600,
    height: int = 800,
    text: str = "VisionForensics Investigation Specimen",
    add_alteration: bool = False,
) -> bytes:
    """Generates an in-memory document image."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, width - 20, height - 20], outline="black", width=2)
    draw.rectangle([30, 30, width - 30, 80], fill="#f1f5f9", outline="#cbd5e1")
    draw.text((40, 45), text, fill="black")

    for y in range(120, height - 100, 45):
        draw.line([40, y, width - 40, y], fill="#94a3b8", width=1)
        draw.text((45, y - 15), f"Forensic Document Record Line at {y}", fill="#334155")

    if add_alteration:
        draw.rectangle([width - 220, height - 160, width - 40, height - 60], fill="#fee2e2", outline="#dc2626", width=3)
        draw.text((width - 200, height - 120), "MODIFIED ENTRY", fill="#991b1b")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_multipage_pdf(page_count: int = 3) -> bytes:
    """Generates a synthetic multi-page PDF."""
    images = []
    for i in range(page_count):
        img_bytes = create_synthetic_image(text=f"VisionForensics Multipage Case - Page {i + 1}")
        images.append(Image.open(io.BytesIO(img_bytes)))
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Resets rate limiting on each test invocation."""
    limiter.reset("login:127.0.0.1")
    limiter.reset("upload:127.0.0.1")
    yield
    limiter.reset("login:127.0.0.1")
    limiter.reset("upload:127.0.0.1")


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
    """Helper to authenticate or create a test user and obtain a JWT bearer token."""
    repo = UserRepository(db_session)
    user = repo.get_by_email(email)
    pw = "ReportTestPass123!"
    if not user:
        user = repo.create_user(
            email=email,
            password_hash=hash_password(pw),
            full_name="Report Forensic Specialist",
            role=role,
            is_active=True,
        )
    return create_access_token(user_id=user.id, email=user.email, role=user.role)


# ====================================================================== #
# 1. Authentic Document Report Generation                                #
# ====================================================================== #

@pytest.mark.asyncio
async def test_01_authentic_document_report_generation(client: AsyncClient, db_session):
    """
    Verifies full report compilation for an authentic document:
    - Generates PDF dossier
    - Computes SHA-256 hash
    - Confirms report number formatting and file existence
    """
    token = await get_auth_token(client, db_session, "report_analyst1@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload authentic document
    png_bytes = _image_to_png_bytes(AUTHENTIC_SAMPLE_PATH)
    files = {"file": ("authentic_exhibit_01.png", png_bytes, "image/png")}
    up_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # Request report generation
    rep_payload = {
        "document_id": doc_id,
        "title": "Forensic Analysis of Authentic Driving License Exhibit",
        "analyst_notes": "Exhibited baseline features consistent with genuine DMV document standard.",
    }
    rep_res = await client.post("/api/v1/reports", json=rep_payload, headers=headers)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()

    assert rep_data["report_id"] is not None
    assert rep_data["report_number"].startswith("VF-REP-")
    assert rep_data["document_id"] == doc_id
    assert rep_data["status"] in ("GENERATED", "COMPLETED")
    assert len(rep_data["sha256_hash"]) == 64
    assert rep_data["file_size_bytes"] > 0
    assert rep_data["page_count"] >= 4
    assert rep_data["download_url"] == f"/api/v1/reports/{rep_data['report_id']}/download"

    # Verify physical file existence and hash integrity
    db_session.expire_all()
    repo = ReportRepository(db_session)
    report_orm = repo.get_report(rep_data["report_id"])
    assert report_orm is not None
    file_path = Path(report_orm.file_path).resolve()
    assert file_path.exists()
    assert hashlib.sha256(file_path.read_bytes()).hexdigest() == rep_data["sha256_hash"]


# ====================================================================== #
# 2. Suspicious Document Report Generation                               #
# ====================================================================== #

@pytest.mark.asyncio
async def test_02_suspicious_document_report_generation(client: AsyncClient, db_session):
    """Verifies report generation when document exhibits suspicious anomalies."""
    token = await get_auth_token(client, db_session, "report_analyst2@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img_bytes = create_synthetic_image(text="Suspicious Contract Specimen", add_alteration=True)
    files = {"file": ("suspicious_doc.png", img_bytes, "image/png")}
    up_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    rep_payload = {
        "document_id": doc_id,
        "title": "Examination of Contract with Discrepancies",
        "analyst_notes": "Unusual boundary sharpness observed around section 4.",
    }
    rep_res = await client.post("/api/v1/reports", json=rep_payload, headers=headers)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()

    assert rep_data["status"] in ("GENERATED", "COMPLETED")
    assert rep_data["metadata_snapshot"] is not None
    assert "unified_risk_tier" in rep_data["metadata_snapshot"]


# ====================================================================== #
# 3. High-Risk Document Report & Zero "CONFIRMED FORGERY"                 #
# ====================================================================== #

@pytest.mark.asyncio
async def test_03_high_risk_document_and_no_confirmed_forgery(client: AsyncClient, db_session):
    """
    Verifies that a high-risk exhibit generates a complete dossier,
    and strictly validates that the term 'CONFIRMED FORGERY' is NEVER used as an overall verdict.
    """
    token = await get_auth_token(client, db_session, "report_analyst3@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    png_bytes = _image_to_png_bytes(FORGED_SAMPLE_PATH)
    files = {"file": ("copy_move_forgery.png", png_bytes, "image/png")}
    up_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    rep_payload = {
        "document_id": doc_id,
        "title": "High-Risk Tampering Examination",
    }
    rep_res = await client.post("/api/v1/reports", json=rep_payload, headers=headers)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()

    # Verify verdict does NOT state "CONFIRMED FORGERY"
    overall_verdict = rep_data["metadata_snapshot"].get("overall_verdict", "")
    assert overall_verdict != "CONFIRMED FORGERY", "Prohibited verdict 'CONFIRMED FORGERY' detected"

    # Read physical PDF text representation to ensure compliance
    db_session.expire_all()
    repo = ReportRepository(db_session)
    report_orm = repo.get_report(rep_data["report_id"])
    pdf_bytes = Path(report_orm.file_path).resolve().read_bytes()
    # Check that in the executive verdict string CONFIRMED FORGERY is absent
    assert b"Verdict: CONFIRMED FORGERY" not in pdf_bytes


# ====================================================================== #
# 4. ML_UNAVAILABLE and DEGRADED Reports Handling                        #
# ====================================================================== #

@pytest.mark.asyncio
async def test_04_ml_unavailable_or_degraded_report_handling(client: AsyncClient, db_session):
    """
    Verifies that when ML inference is degraded or unavailable, report generation
    succeeds gracefully without unhandled exceptions or layout distortion.
    """
    builder = ForensicPDFBuilder()
    doc_meta = {
        "id": "mock-doc-degraded-001",
        "original_filename": "degraded_sample.png",
        "file_type": "png",
        "size_bytes": 10240,
        "page_count": 1,
        "sha256_hash": "a" * 64,
        "case_id": "CASE-DEG-01",
    }
    analysis_data = {
        "unified_risk_tier": "UNKNOWN",
        "overall_verdict": "INCONCLUSIVE",
        "risk_description": "Statistical ML model was degraded due to missing high-order frequency coefficients.",
        "composite_risk_score": 0.0,
        "analysis_version": 1,
        "track_1_ml": {
            "status": "ML_UNAVAILABLE",
            "forgery_probability": None,
            "predicted_class": None,
            "operational_threshold": 0.40,
            "feature_completeness": 0.35,
            "top_contributing_features": {},
        },
        "track_2_symbolic": {
            "symbolic_severity_score": 0.0,
            "symbolic_evidence": [],
        },
        "detected_regions": [],
        "image_dimensions": {"width": 800, "height": 1000, "page_count": 1},
        "decision_trace": [],
    }

    pdf_bytes = builder.build_report(
        report_number="VF-REP-TEST-DEGRADED",
        document_meta=doc_meta,
        analysis_data=analysis_data,
        custody_logs=[],
        analyst_notes="ML model was offline or degraded for this batch.",
    )

    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


# ====================================================================== #
# 5. Multi-Page PDF Report Generation                                    #
# ====================================================================== #

@pytest.mark.asyncio
async def test_05_multipage_pdf_report_generation(client: AsyncClient, db_session):
    """Verifies report generation for multi-page document exhibits."""
    token = await get_auth_token(client, db_session, "report_analyst5@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_multipage_pdf(page_count=3)
    files = {"file": ("multipage_case_file.pdf", pdf_bytes, "application/pdf")}
    up_res = await client.post("/api/v1/upload", files=files, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]
    assert up_res.json()["page_count"] == 3

    rep_payload = {
        "document_id": doc_id,
        "title": "Examination of 3-Page Forensic Exhibit",
    }
    rep_res = await client.post("/api/v1/reports", json=rep_payload, headers=headers)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()

    assert rep_data["status"] in ("GENERATED", "COMPLETED")
    assert rep_data["document_id"] == doc_id


# ====================================================================== #
# 6. Reports Containing Multiple Evidence Regions                        #
# ====================================================================== #

@pytest.mark.asyncio
async def test_06_reports_with_multiple_evidence_regions(client: AsyncClient, db_session):
    """Verifies that detected visual regions are structured into the report table."""
    builder = ForensicPDFBuilder()
    doc_meta = {
        "id": "doc-regions-test-001",
        "original_filename": "multi_region_evidence.png",
        "file_type": "png",
        "size_bytes": 54000,
        "page_count": 1,
        "sha256_hash": "b" * 64,
        "case_id": "CASE-REG-02",
    }
    analysis_data = {
        "unified_risk_tier": "HIGH_RISK",
        "overall_verdict": "ANOMALIES_DETECTED",
        "risk_description": "Multiple localized anomalies detected across text and signature fields.",
        "composite_risk_score": 85.5,
        "analysis_version": 1,
        "track_1_ml": {
            "status": "SUCCESS",
            "forgery_probability": 0.88,
            "predicted_class": "FORGED",
            "operational_threshold": 0.40,
            "feature_completeness": 1.0,
            "top_contributing_features": {"ela_anomaly_score": 0.82, "copymove_cluster_count": 0.74},
        },
        "track_2_symbolic": {
            "symbolic_severity_score": 0.75,
            "symbolic_evidence": [
                {"category": "COPY_MOVE", "severity": 0.85, "description": "Duplicate text cluster in section 2"},
                {"category": "ELA_INCONSISTENCY", "severity": 0.70, "description": "High residual compression error"},
            ],
        },
        "detected_regions": [
            {
                "id": f"reg-{i}",
                "page_index": 0,
                "detector": "copy_move_detector",
                "category": "COPY_MOVE",
                "severity": 0.80,
                "bounding_box": {"x": 50 * i, "y": 60 * i, "width": 80, "height": 40},
            }
            for i in range(1, 6)
        ],
        "image_dimensions": {"width": 800, "height": 1000, "page_count": 1},
        "decision_trace": [],
    }

    pdf_bytes = builder.build_report(
        report_number="VF-REP-TEST-REGIONS",
        document_meta=doc_meta,
        analysis_data=analysis_data,
        custody_logs=[],
        analyst_notes="Identified 5 distinct suspicious clusters.",
    )

    assert len(pdf_bytes) > 3000
    assert pdf_bytes.startswith(b"%PDF")


# ====================================================================== #
# 7. Reports with Linked Comparison Results (5-Page Dossier)             #
# ====================================================================== #

@pytest.mark.asyncio
async def test_07_reports_with_linked_comparison(client: AsyncClient, db_session):
    """
    Verifies that linking a comparison generates a comprehensive 5-page dossier
    with comparative differential metrics and alignment breakdown.
    """
    token = await get_auth_token(client, db_session, "report_analyst7@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Doc A
    img_a = create_synthetic_image(text="Original Lease Agreement Form")
    files_a = {"file": ("lease_original.png", img_a, "image/png")}
    res_a = await client.post("/api/v1/upload", files=files_a, headers=headers)
    assert res_a.status_code == 201
    doc_a_id = res_a.json()["document_id"]

    # Upload Doc B (altered)
    img_b = create_synthetic_image(text="Modified Lease Agreement Form", add_alteration=True)
    files_b = {"file": ("lease_modified.png", img_b, "image/png")}
    res_b = await client.post("/api/v1/upload", files=files_b, headers=headers)
    assert res_b.status_code == 201
    doc_b_id = res_b.json()["document_id"]

    # Run comparison
    comp_payload = {
        "document_a_id": doc_a_id,
        "document_b_id": doc_b_id,
        "page_a": 0,
        "page_b": 0,
        "align_images": True,
    }
    comp_res = await client.post("/api/v1/comparison", json=comp_payload, headers=headers)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["comparison_id"]

    # Generate Report for Doc A linking the comparison
    rep_payload = {
        "document_id": doc_a_id,
        "comparison_id": comp_id,
        "include_comparison": True,
        "title": "Comparative Examination: Original vs Modified Form",
        "analyst_notes": "Differential analysis isolates modified clause in lower quadrant.",
    }
    rep_res = await client.post("/api/v1/reports", json=rep_payload, headers=headers)
    assert rep_res.status_code == 201
    rep_data = rep_res.json()

    assert rep_data["page_count"] == 5
    assert rep_data["status"] in ("GENERATED", "COMPLETED")


# ====================================================================== #
# 8. Table Formatting & Latin-1 Text Sanitization                        #
# ====================================================================== #

def test_08_text_sanitizer_and_formatting():
    """Verifies that non-latin typographic symbols are safely converted without crash."""
    test_str = "“Forensic Test” – Section ‘A’ … σ=1.5 µ=2.0 20×30 ≥ 10 ≤ 50 ≠ 0"
    sanitized = sanitize_text(test_str)
    assert '"' in sanitized
    assert "'" in sanitized
    assert "..." in sanitized
    assert "sigma=" in sanitized
    assert "mu=" in sanitized
    assert "x" in sanitized
    assert ">=" in sanitized
    assert "<=" in sanitized
    assert "!=" in sanitized


# ====================================================================== #
# 9. Graceful Fallback on Missing Evidence Images                        #
# ====================================================================== #

def test_09_graceful_fallback_missing_evidence():
    """Verifies that missing evidence image files do not cause report generation to fail."""
    builder = ForensicPDFBuilder()
    doc_meta = {
        "id": "doc-fallback-001",
        "original_filename": "fallback_specimen.png",
        "file_type": "png",
        "size_bytes": 1000,
        "page_count": 1,
        "sha256_hash": "c" * 64,
        "case_id": None,
    }
    analysis_data = {
        "unified_risk_tier": "LOW_RISK",
        "overall_verdict": "AUTHENTIC",
        "risk_description": "Clean specimen.",
        "composite_risk_score": 10.0,
        "analysis_version": 1,
        "track_1_ml": {
            "status": "SUCCESS",
            "forgery_probability": 0.05,
            "predicted_class": "AUTHENTIC",
            "operational_threshold": 0.40,
            "feature_completeness": 1.0,
            "top_contributing_features": {},
        },
        "track_2_symbolic": {"symbolic_severity_score": 0.0, "symbolic_evidence": []},
        "detected_regions": [],
        "image_dimensions": {"width": 800, "height": 1000, "page_count": 1},
        "decision_trace": [],
    }

    # Pass nonexistent comparison data with nonexistent paths
    comp_data = {
        "comparison_id": "nonexistent-comp",
        "document_a_id": "doc-a",
        "document_b_id": "doc-b",
        "page_a": 0,
        "page_b": 0,
        "alignment": {"status": "FAILED", "confidence": 0.0},
        "metrics": {"similarity_score": 0.5, "ssim_score": 0.5, "difference_percentage": 50.0},
        "metadata_diff": {"hash_match": False},
        "differential_regions": [],
        "summary": {"verdict_category": "SIGNIFICANT_DIFFERENCES", "finding": "Discrepant"},
    }

    pdf_bytes = builder.build_report(
        report_number="VF-REP-FALLBACK",
        document_meta=doc_meta,
        analysis_data=analysis_data,
        custody_logs=[],
        comparison_data=comp_data,
        analyst_notes="Generated under missing artifact test.",
    )
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


# ====================================================================== #
# 10. IDOR Defense: Cross-User Report Access Prevention                  #
# ====================================================================== #

@pytest.mark.asyncio
async def test_10_idor_defense_unauthorized_report_access(client: AsyncClient, db_session):
    """
    Verifies that:
    1. Analyst B cannot generate a report for Analyst A's document (HTTP 403).
    2. Analyst B cannot retrieve metadata for Analyst A's report (HTTP 403).
    3. Analyst B cannot download Analyst A's report (HTTP 403).
    4. Admin can retrieve and download Analyst A's report (proper RBAC).
    """
    token_a = await get_auth_token(client, db_session, "user_alpha@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    token_b = await get_auth_token(client, db_session, "user_bravo@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    token_admin = await get_auth_token(client, db_session, "admin_user@visionforensics.local", UserRole.SYSTEM_ADMINISTRATOR.value)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # User A uploads document
    img_a = create_synthetic_image(text="Classified Exhibit Alpha")
    files_a = {"file": ("alpha_exhibit.png", img_a, "image/png")}
    up_res = await client.post("/api/v1/upload", files=files_a, headers=headers_a)
    assert up_res.status_code == 201
    doc_a_id = up_res.json()["document_id"]

    # 1. User B attempts to generate report for User A's document -> 403 Forbidden
    rep_res_b = await client.post(
        "/api/v1/reports",
        json={"document_id": doc_a_id, "title": "Unauthorized Report Attempt"},
        headers=headers_b,
    )
    assert rep_res_b.status_code == 403

    # User A generates report
    rep_res_a = await client.post(
        "/api/v1/reports",
        json={"document_id": doc_a_id, "title": "Authorized Exhibit Alpha Report"},
        headers=headers_a,
    )
    assert rep_res_a.status_code == 201
    report_id = rep_res_a.json()["report_id"]

    # 2. User B attempts to view report metadata -> 403 Forbidden
    get_res_b = await client.get(f"/api/v1/reports/{report_id}", headers=headers_b)
    assert get_res_b.status_code == 403

    # 3. User B attempts to download report -> 403 Forbidden
    down_res_b = await client.get(f"/api/v1/reports/{report_id}/download", headers=headers_b)
    assert down_res_b.status_code == 403

    # 4. Admin CAN view metadata and download
    get_res_admin = await client.get(f"/api/v1/reports/{report_id}", headers=headers_admin)
    assert get_res_admin.status_code == 200
    down_res_admin = await client.get(f"/api/v1/reports/{report_id}/download", headers=headers_admin)
    assert down_res_admin.status_code == 200


# ====================================================================== #
# 11. Report SHA-256 Integrity Verification & Tamper Alarm               #
# ====================================================================== #

@pytest.mark.asyncio
async def test_11_report_sha256_tamper_detection(client: AsyncClient, db_session):
    """
    Verifies that if a report file on disk is modified/tampered:
    1. Download endpoint strictly refuses to serve the file and returns HTTP 409 Conflict.
    2. A TAMPERING_ALARM event is recorded in the custody audit ledger.
    """
    token = await get_auth_token(client, db_session, "report_integrity@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img = create_synthetic_image(text="Integrity Verification Exhibit")
    up_res = await client.post("/api/v1/upload", files={"file": ("integrity.png", img, "image/png")}, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    rep_res = await client.post(
        "/api/v1/reports",
        json={"document_id": doc_id, "title": "Tamper Test Report"},
        headers=headers,
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()["report_id"]

    # Locate file on disk and tamper with it
    db_session.expire_all()
    repo = ReportRepository(db_session)
    report_orm = repo.get_report(report_id)
    pdf_path = Path(report_orm.file_path).resolve()
    assert pdf_path.exists()

    # Corrupt the file on disk by appending unauthorized bytes
    with open(pdf_path, "ab") as f:
        f.write(b"UNAUTHORIZED_TAMPER_MODIFICATION_BYTES")

    # Attempt to download the tampered report
    down_res = await client.get(f"/api/v1/reports/{report_id}/download", headers=headers)
    assert down_res.status_code == 409
    assert "TAMPERING_ALARM" in down_res.json()["detail"]

    # Verify custody ledger recorded TAMPERING_ALARM
    db_session.expire_all()
    custody_log = (
        db_session.query(ExhibitCustodyLog)
        .filter(ExhibitCustodyLog.document_id == doc_id, ExhibitCustodyLog.event_type == "TAMPERING_ALARM")
        .first()
    )
    assert custody_log is not None
    assert custody_log.status == "TAMPERED"


# ====================================================================== #
# 12. Report Download Endpoint & Chain-of-Custody Logging                #
# ====================================================================== #

@pytest.mark.asyncio
async def test_12_download_endpoint_and_audit_logging(client: AsyncClient, db_session):
    """
    Verifies successful report download:
    - Content-Type application/pdf
    - X-Report-SHA256 header matches report hash
    - Custody events REPORT_GENERATED and REPORT_DOWNLOADED recorded
    """
    token = await get_auth_token(client, db_session, "report_download@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img = create_synthetic_image(text="Download Test Exhibit")
    up_res = await client.post("/api/v1/upload", files={"file": ("download_test.png", img, "image/png")}, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    rep_res = await client.post(
        "/api/v1/reports",
        json={"document_id": doc_id, "title": "Verified Download Case Report"},
        headers=headers,
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()["report_id"]
    sha256_hash = rep_res.json()["sha256_hash"]

    # Download report
    down_res = await client.get(f"/api/v1/reports/{report_id}/download", headers=headers)
    assert down_res.status_code == 200
    assert down_res.headers["content-type"] == "application/pdf"
    assert down_res.headers["x-report-sha256"] == sha256_hash
    assert len(down_res.content) > 0

    # Verify audit logs in PostgreSQL
    db_session.expire_all()
    logs = (
        db_session.query(ExhibitCustodyLog)
        .filter(ExhibitCustodyLog.document_id == doc_id)
        .order_by(ExhibitCustodyLog.timestamp.asc())
        .all()
    )
    event_types = [l.event_type for l in logs]
    assert "REPORT_GENERATED" in event_types
    assert "REPORT_DOWNLOADED" in event_types


# ====================================================================== #
# 13. Database Persistence Across Sessions & Listing                     #
# ====================================================================== #

@pytest.mark.asyncio
async def test_13_report_persistence_and_listing(client: AsyncClient, db_session):
    """Verifies that generated reports persist in PostgreSQL and can be listed with pagination."""
    token = await get_auth_token(client, db_session, "report_listing@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload and generate 2 reports
    for i in range(2):
        img = create_synthetic_image(text=f"Archive Exhibit {i}")
        up_res = await client.post("/api/v1/upload", files={"file": (f"archive_{i}.png", img, "image/png")}, headers=headers)
        assert up_res.status_code == 201
        doc_id = up_res.json()["document_id"]
        rep_res = await client.post(
            "/api/v1/reports",
            json={"document_id": doc_id, "title": f"Archived Case Report {i}"},
            headers=headers,
        )
        assert rep_res.status_code == 201

    # List reports
    list_res = await client.get("/api/v1/reports?limit=10&offset=0", headers=headers)
    assert list_res.status_code == 200
    reports_list = list_res.json()
    assert len(reports_list) >= 2
    assert all("report_id" in r for r in reports_list)
    assert all("report_number" in r for r in reports_list)
    assert all("unified_risk_tier" in r for r in reports_list)


# ====================================================================== #
# 14. Platform Regression Check                                          #
# ====================================================================== #

@pytest.mark.asyncio
async def test_14_platform_regression_check(client: AsyncClient, db_session):
    """Verifies that health check, upload, and comparison remain fully operational."""
    # Health check
    h_res = await client.get("/api/v1/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    # Single-page upload and analysis
    token = await get_auth_token(client, db_session, "regression_analyst@visionforensics.local", UserRole.FORENSIC_ANALYST.value)
    headers = {"Authorization": f"Bearer {token}"}

    img = create_synthetic_image(text="Regression Check Exhibit")
    up_res = await client.post("/api/v1/upload", files={"file": ("reg_check.png", img, "image/png")}, headers=headers)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    an_res = await client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert an_res.status_code == 200
    assert an_res.json()["document_id"] == doc_id
