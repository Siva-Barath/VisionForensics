"""
test_phase8r_remediation.py — Comprehensive Unit & Integration Verification Suite for Phase 8R.
Verifies REM-01 through REM-04 implementations and model governance invariants.
"""

import math
import hashlib
import io
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

from app.pipeline.context import AnalysisContext
from app.ml.feature_extractor import FeatureExtractor
from app.services.ml_inference import MLInferenceService, RiskTier, InferenceStatus
from app.services.forensics.jpeg_quality_estimator import (
    estimate_jpeg_quality_from_dqt,
    estimate_jpeg_quality_from_bytes,
    inspect_compression_quality,
)
from app.pipeline.stages.ml_inference_stage import MLInferenceStage
from app.pipeline.stages.risk_stage import RiskStage
from app.services.preprocessing.models import QualityMetrics

FROZEN_RF_SHA256 = "f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280"


# -----------------------------------------------------------------------------
# Test 1: Model SHA-256 Governance Invariant
# -----------------------------------------------------------------------------
def test_frozen_model_sha256_invariant():
    model_path = Path("backend/app/ml/artifacts/random_forest.joblib")
    assert model_path.exists(), "Frozen Random Forest model artifact missing"
    with open(model_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert file_hash == FROZEN_RF_SHA256, (
        f"CRITICAL INVARIANT VIOLATION: Model hash changed! Expected {FROZEN_RF_SHA256}, got {file_hash}"
    )


# -----------------------------------------------------------------------------
# Test 2: REM-01 Per-Page Feature Extraction & Inference
# -----------------------------------------------------------------------------
def test_rem01_per_page_feature_extraction():
    extractor = FeatureExtractor()
    ctx = AnalysisContext()
    ctx.original_filename = "test_multipage.pdf"
    ctx.file_type = "pdf"

    # Page 0: Authentic-like metrics
    ctx.quality_metrics = [
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
    ]
    ctx.image_forensics_metrics = [
        {
            "laplacian_variance": 120.0,
            "blur_severity": 10.0,
            "noise_sigma": 3.0,
            "edge_density": 0.05,
            "illumination_std": 15.0,
            "ela_region_count": 0,
            "ela_max_difference": 12.0,
            "entropy_score": 6.8,
        },
        # Page 1: Altered metrics with strong ELA difference
        {
            "laplacian_variance": 220.0,
            "blur_severity": 35.0,
            "noise_sigma": 8.0,
            "edge_density": 0.15,
            "illumination_std": 35.0,
            "ela_region_count": 4,
            "ela_max_difference": 85.0,
            "entropy_score": 7.6,
        },
    ]

    # Verify document-level extractor averages metrics
    doc_vec = extractor.extract(ctx)
    assert doc_vec.features["img_ela_max_difference_mean"] == (12.0 + 85.0) / 2.0

    # Verify per-page extraction does NOT average metrics
    page_0_vec = extractor.extract_page(ctx, page_index=0)
    assert page_0_vec.features["img_ela_max_difference_mean"] == 12.0
    assert page_0_vec.features["img_laplacian_variance_mean"] == 120.0

    page_1_vec = extractor.extract_page(ctx, page_index=1)
    assert page_1_vec.features["img_ela_max_difference_mean"] == 85.0
    assert page_1_vec.features["img_laplacian_variance_mean"] == 220.0


def test_rem01_per_page_inference_execution():
    service = MLInferenceService()
    ctx = AnalysisContext()
    ctx.original_filename = "test_multipage.pdf"
    ctx.file_type = "pdf"
    ctx.quality_metrics = [
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
    ]
    ctx.image_forensics_metrics = [
        {"laplacian_variance": 120.0, "blur_severity": 10.0, "noise_sigma": 3.0, "edge_density": 0.05, "illumination_std": 15.0, "ela_region_count": 0, "ela_max_difference": 10.0, "entropy_score": 6.8},
        {"laplacian_variance": 240.0, "blur_severity": 40.0, "noise_sigma": 12.0, "edge_density": 0.18, "illumination_std": 45.0, "ela_region_count": 5, "ela_max_difference": 95.0, "entropy_score": 7.8},
    ]

    res_p0 = service.predict_page(ctx, page_index=0)
    res_p1 = service.predict_page(ctx, page_index=1)

    assert res_p0.status in (InferenceStatus.SUCCESS, InferenceStatus.DEGRADED)
    assert res_p1.status in (InferenceStatus.SUCCESS, InferenceStatus.DEGRADED)
    assert res_p0.forgery_probability is not None
    assert res_p1.forgery_probability is not None
    # Altered page 1 must have substantially higher forgery probability than page 0
    assert res_p1.forgery_probability > res_p0.forgery_probability


# -----------------------------------------------------------------------------
# Test 3: REM-02 Multi-Page Risk Aggregation Gate
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rem02_multipage_risk_aggregation_corroborated():
    stage = MLInferenceStage()
    ctx = AnalysisContext()
    ctx.original_filename = "multipage_forged.pdf"
    ctx.file_type = "pdf"
    ctx.page_images = ["p0.png", "p1.png"]
    ctx.quality_metrics = [
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
        QualityMetrics(width=800, height=1000, aspect_ratio=0.8, color_channels=3),
    ]
    # Page 0 authentic, Page 1 elevated
    ctx.image_forensics_metrics = [
        {"laplacian_variance": 120.0, "blur_severity": 10.0, "noise_sigma": 3.0, "edge_density": 0.05, "illumination_std": 15.0, "ela_region_count": 0, "ela_max_difference": 10.0, "entropy_score": 6.8},
        {"laplacian_variance": 250.0, "blur_severity": 45.0, "noise_sigma": 14.0, "edge_density": 0.20, "illumination_std": 50.0, "ela_region_count": 6, "ela_max_difference": 110.0, "entropy_score": 7.9},
    ]
    # Independent visual region detected on Page 1
    ctx.detected_regions = [{
        "id": "reg_1",
        "category": "IMAGE",
        "page_index": 1,
        "severity": 85.0,
    }]

    res = await stage.run(ctx)
    assert res.status == "success"
    assert len(ctx.pages_ml) == 2
    assert ctx.ml_prediction is not None
    # Forged page 1 corroborated with visual evidence elevates document to FORGED / HIGH_RISK
    assert ctx.ml_prediction["predicted_class"] == "FORGED"
    assert ctx.ml_prediction["risk_tier"] == "HIGH_RISK"


# -----------------------------------------------------------------------------
# Test 4: REM-03 Independent Visual Evidence Arbiter (Copy-Move Recovery)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rem03_visual_evidence_arbiter_copymove_elevation():
    stage = RiskStage()
    ctx = AnalysisContext()
    ctx.original_filename = "exhibit_copymove.tif"
    ctx.file_type = "tif"

    # Track 1 ML has low probability (simulating physical substrate false negative)
    ctx.ml_prediction = {
        "status": "SUCCESS",
        "forgery_probability": 0.2871,
        "predicted_class": "AUTHENTIC",
        "risk_tier": "LOW_RISK",
        "operational_threshold": 0.40,
        "limitations": [],
    }

    # Track 3 Visual Evidence has verified copy-move clusters
    ctx.copy_move_features = {
        "inlier_matches": 18,
        "descriptor_matches": 45,
        "confidence": 0.82,
        "duplicate_pair_count": 5,
    }
    ctx.detected_regions = [
        {
            "id": f"cm_{i}",
            "detector": "copy_move_region_analyzer",
            "category": "COPY_MOVE",
            "severity": 90.0,
            "confidence": 0.82,
            "page_index": 0,
        }
        for i in range(5)
    ]

    res = await stage.run(ctx)
    assert res.status == "success"
    # Track 1 ML probability must remain strictly unchanged
    assert ctx.risk_assessment["track_1_ml"]["forgery_probability"] == 0.2871
    # Track 3 Visual Evidence Arbiter elevates Unified Risk to HIGH_RISK
    assert ctx.risk_assessment["unified_risk_tier"] == "HIGH_RISK"
    assert ctx.risk_assessment["overall_verdict"] == "SUSPICIOUS / HIGH_RISK"
    assert ctx.risk_assessment["track_3_visual"]["copy_move_confirmed"] is True


@pytest.mark.asyncio
async def test_rem03_repetitive_guilloche_pattern_not_elevated():
    stage = RiskStage()
    ctx = AnalysisContext()
    ctx.original_filename = "authentic_guilloche.png"
    ctx.file_type = "png"

    # Track 1 ML Authentic
    ctx.ml_prediction = {
        "status": "SUCCESS",
        "forgery_probability": 0.18,
        "predicted_class": "AUTHENTIC",
        "risk_tier": "LOW_RISK",
        "operational_threshold": 0.40,
        "limitations": [],
    }

    # Routine background repetitive texture (low inliers < 15, low confidence < 0.80)
    ctx.copy_move_features = {
        "inlier_matches": 4,
        "descriptor_matches": 12,
        "confidence": 0.45,
        "duplicate_pair_count": 1,
    }

    res = await stage.run(ctx)
    assert res.status == "success"
    # False-positive guard prevents elevation
    assert ctx.risk_assessment["unified_risk_tier"] == "LOW_RISK"
    assert ctx.risk_assessment["overall_verdict"] == "LOW_RISK / AUTHENTIC"


# -----------------------------------------------------------------------------
# Test 5: REM-04 Non-Destructive JPEG Quality Qualification
# -----------------------------------------------------------------------------
def test_rem04_jpeg_quality_estimation_grid():
    for q_target in [20, 35, 40, 50, 75, 90]:
        buf = io.BytesIO()
        img = Image.new("RGB", (120, 120), color=(128, 128, 128))
        img.save(buf, format="JPEG", quality=q_target)
        buf.seek(0)
        q_est = estimate_jpeg_quality_from_bytes(buf.getvalue())
        assert q_est is not None
        # Must be accurate within +/- 2 quality units
        assert abs(q_est - q_target) <= 2.0, f"Q mismatch: target {q_target}, got {q_est}"


@pytest.mark.asyncio
async def test_rem04_severe_jpeg_borderline_qualification():
    stage = RiskStage()
    ctx = AnalysisContext()
    ctx.original_filename = "exhibit_11_diff_heavy_jpeg.jpg"
    ctx.file_type = "jpeg"

    # Generate JPEG with Q=25
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    img.save(buf, format="JPEG", quality=25)
    ctx.file_bytes = buf.getvalue()

    # Borderline ML prediction (e.g. 0.4129 like EX-11)
    ctx.ml_prediction = {
        "status": "SUCCESS",
        "forgery_probability": 0.4129,
        "predicted_class": "FORGED",
        "risk_tier": "SUSPICIOUS",
        "operational_threshold": 0.40,
        "limitations": [],
    }

    res = await stage.run(ctx)
    assert res.status == "success"
    # REM-04 qualifies borderline prediction
    assert ctx.risk_assessment["overall_verdict"] == "SUSPICIOUS / COMPRESSION_DEGRADED"
    assert ctx.risk_assessment["unified_risk_tier"] == "SUSPICIOUS"
    assert ctx.risk_assessment["track_1_ml"]["predicted_class"] == "AUTHENTIC"
    # Limitation notice attached
    assert any(
        lim.get("code") == "HEAVY_COMPRESSION_ARTIFACTS"
        for lim in ctx.ml_prediction["limitations"]
    )
