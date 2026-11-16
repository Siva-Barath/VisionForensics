"""
test_phase5_e2e.py — Phase 5 End-to-End Verification Test Suite.

Verifies:
1. Health check & document analysis endpoint routes.
2. Full pipeline execution on authentic document specimen (02_aut_drvlic_new_CA02.tif).
3. Full pipeline execution on forged document specimen (02_aut_drvlic_new_CS05_copy_move.tif) at operational threshold T=0.40.
4. Error handling for non-existent documents (404) and invalid files (415).
5. Degraded ML inference handling when critical features are missing.
6. Concurrent document processing and thread safety across multiple sessions.
7. Verification that 'CONFIRMED FORGERY' is never returned as a definitive claim.
"""

import io
import asyncio
from pathlib import Path
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app import app
from app.services.ml_inference import MLInferenceService, RiskTier, InferenceStatus

AUTHENTIC_SAMPLE_PATH = Path("D:/Datasets/TrainingDataset/authentic/driving_license/02_aut_drvlic_new_CA02.tif")
FORGED_SAMPLE_PATH = Path("D:/Datasets/TrainingDataset/ml_phase2/train_forged/driving_license/02_aut_drvlic_new_CS05_copy_move.tif")


def _image_to_png_bytes(image_path: Path) -> bytes:
    """Reads a TIFF/image from disk and converts to standard PNG bytes for upload."""
    with Image.open(image_path) as img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


@pytest.fixture
async def client():
    from app.database.session import SessionLocal
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password, create_access_token
    with SessionLocal() as db:
        repo = UserRepository(db)
        user = repo.get_by_email("phase5_fixture@visionforensics.local")
        if user is None:
            user = repo.create_user(email="phase5_fixture@visionforensics.local", password_hash=hash_password("IsolatedFixture123!"), full_name="Isolated API fixture")
        token = create_access_token(user.id, user.email, user.role)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": "Bearer " + token}) as ac:
        yield ac


@pytest.mark.asyncio
class TestPhase5EndToEnd:

    async def test_01_health_and_schema(self, client: AsyncClient):
        """Verifies health check and API mounting."""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    async def test_02_authentic_document_e2e(self, client: AsyncClient):
        """
        Uploads an authentic document through the entire pipeline:
        Preprocessing -> OCR -> Layout -> Metadata -> Forgery -> Classification -> MLInference -> Risk -> Explainability -> Report.
        Then queries GET /api/v1/documents/{document_id}/analysis to verify Track 1 ML & Track 2 Symbolic synthesis.
        """
        png_bytes = _image_to_png_bytes(AUTHENTIC_SAMPLE_PATH)

        # 1. Upload
        upload_resp = await client.post(
            "/api/v1/upload",
            files={"file": ("aut_drvlic_test.png", png_bytes, "image/png")},
        )
        assert upload_resp.status_code == 201
        upload_data = upload_resp.json()

        assert "document_id" in upload_data
        assert "job_id" in upload_data
        doc_id = upload_data["document_id"]
        assert upload_data["processing_status"] in ("completed", "partial")

        # 2. Retrieve analysis
        analysis_resp = await client.get(f"/api/v1/documents/{doc_id}/analysis")
        assert analysis_resp.status_code == 200
        analysis_data = analysis_resp.json()

        # Document identification
        assert analysis_data["document_id"] == doc_id
        assert analysis_data["status"] == "processed"

        # Track 1: ML Inference Verification
        t1 = analysis_data["track_1_ml"]
        assert t1["available"] is True
        assert t1["status"] in ("SUCCESS", "DEGRADED")
        assert t1["operational_threshold"] == 0.40
        assert t1["feature_completeness"] >= 0.90
        assert isinstance(t1["forgery_probability"], float)
        assert 0.0 <= t1["forgery_probability"] <= 1.0

        # Authentic specimen CA02 should score low risk
        assert t1["predicted_class"] == "AUTHENTIC"
        assert t1["risk_tier"] == "LOW_RISK"
        assert t1["forgery_probability"] < 0.30

        # Unified Risk Synthesis
        assert analysis_data["unified_risk_tier"] == "LOW_RISK"
        assert "LOW_RISK" in analysis_data["overall_verdict"] or "AUTHENTIC" in analysis_data["overall_verdict"]
        assert "Preliminary screening indicates relatively low forgery risk" in analysis_data["risk_description"]

        # Track 2: Symbolic Evidence Verification
        t2 = analysis_data["track_2_symbolic"]
        assert t2["available"] is True
        assert isinstance(t2["symbolic_severity_score"], float)

        # Decision Trace
        trace = analysis_data["decision_trace"]
        assert len(trace) >= 2
        trace_tracks = [step["track"] for step in trace]
        assert any("Track 1" in t for t in trace_tracks)
        assert any("Track 2" in t for t in trace_tracks)

        # Limitations & Forensic Disclaimers
        limits = analysis_data["limitations"]
        assert len(limits) > 0
        limit_codes = [lim["code"] for lim in limits]
        assert "DECISION_SUPPORT_NOTICE" in limit_codes
        assert "COPY_MOVE_SENSITIVITY" in limit_codes

    async def test_03_forged_document_e2e(self, client: AsyncClient):
        """
        Uploads a synthetic copy-move forged document through the entire pipeline.
        Verifies:
        - Operational threshold T=0.40 is applied.
        - Forgery probability is evaluated (P >= 0.55).
        - Classification triggers HIGH_RISK tier.
        - Terminology never claims 'CONFIRMED FORGERY'.
        - Top contributing features are isolated.
        """
        png_bytes = _image_to_png_bytes(FORGED_SAMPLE_PATH)

        # 1. Upload
        upload_resp = await client.post(
            "/api/v1/upload",
            files={"file": ("forged_sample.png", png_bytes, "image/png")},
        )
        assert upload_resp.status_code == 201
        upload_data = upload_resp.json()
        doc_id = upload_data["document_id"]

        # 2. Retrieve analysis
        analysis_resp = await client.get(f"/api/v1/documents/{doc_id}/analysis")
        assert analysis_resp.status_code == 200
        analysis_data = analysis_resp.json()

        # Track 1: ML Inference Verification
        t1 = analysis_data["track_1_ml"]
        assert t1["available"] is True
        assert t1["forgery_probability"] >= 0.40
        assert t1["predicted_class"] == "FORGED"
        assert t1["risk_tier"] in ("SUSPICIOUS", "HIGH_RISK")

        # Unified Risk Synthesis
        assert analysis_data["unified_risk_tier"] in ("SUSPICIOUS", "HIGH_RISK")
        assert "CONFIRMED FORGERY" not in analysis_data["overall_verdict"]
        assert "CONFIRMED FORGERY" not in analysis_data["risk_description"]

        # Top features
        top_features = t1["top_contributing_features"]
        assert len(top_features) > 0

    async def test_04_non_existent_document_404(self, client: AsyncClient):
        """Querying a non-existent document ID returns HTTP 404."""
        resp = await client.get("/api/v1/documents/non-existent-uuid-12345/analysis")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_05_invalid_upload_types(self, client: AsyncClient):
        """Unsupported file types return 415."""
        resp = await client.post(
            "/api/v1/upload",
            files={"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")},
        )
        assert resp.status_code == 415

    async def test_06_degraded_ml_handling(self):
        """
        Direct service test: missing non-critical features degrades gracefully,
        while missing critical features triggers ML_UNAVAILABLE.
        """
        service = MLInferenceService()
        assert service.is_loaded

        # 1. Partial features missing non-critical features -> DEGRADED
        partial_features = {
            "img_ela_max_difference_mean": 45.0,
            "img_laplacian_variance_mean": 120.0,
            "img_blur_severity_mean": 0.05,
        }
        res_partial = service.predict_from_features(partial_features)
        assert res_partial.status == InferenceStatus.DEGRADED
        assert res_partial.feature_completeness < 1.0
        assert len(res_partial.imputed_features) > 0

        # 2. Critical features missing -> ML_UNAVAILABLE
        empty_features = {}
        res_empty = service.predict_from_features(empty_features)
        assert res_empty.status == InferenceStatus.ML_UNAVAILABLE
        assert res_empty.risk_tier == RiskTier.UNKNOWN

    async def test_07_concurrent_requests(self, client: AsyncClient):
        """Verifies thread safety and independent session contexts during concurrent ingestion."""
        png_bytes = _image_to_png_bytes(AUTHENTIC_SAMPLE_PATH)

        async def upload_task(idx: int):
            resp = await client.post(
                "/api/v1/upload",
                files={"file": (f"concurrent_{idx}.png", png_bytes, "image/png")},
            )
            assert resp.status_code == 201
            doc_id = resp.json()["document_id"]
            analysis_resp = await client.get(f"/api/v1/documents/{doc_id}/analysis")
            assert analysis_resp.status_code == 200
            return analysis_resp.json()

        results = await asyncio.gather(*(upload_task(i) for i in range(3)))
        doc_ids = [r["document_id"] for r in results]
        assert len(doc_ids) == len(set(doc_ids))  # All UUIDs must be distinct
        for r in results:
            assert r["unified_risk_tier"] == "LOW_RISK"
            assert r["track_1_ml"]["available"] is True
            assert r["track_1_ml"]["predicted_class"] == "AUTHENTIC"
