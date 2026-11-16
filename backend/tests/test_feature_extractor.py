"""
Tests for FeatureExtractor.

All tests use a synthetic AnalysisContext — no real files, no pipeline.
"""
import pytest
from unittest.mock import MagicMock

from app.pipeline.context import AnalysisContext
from app.ml.feature_extractor import FeatureExtractor
from app.ml.feature_registry import FEATURE_NAMES


@pytest.fixture
def extractor():
    return FeatureExtractor()


def _make_quality_metrics(width=2480, height=3508, aspect_ratio=0.707, color_channels=3):
    qm = MagicMock()
    qm.width = width
    qm.height = height
    qm.aspect_ratio = aspect_ratio
    qm.color_channels = color_channels
    return qm


@pytest.fixture
def empty_context():
    return AnalysisContext(original_filename="test.png", file_type="png")


@pytest.fixture
def full_context():
    ctx = AnalysisContext(original_filename="doc.pdf", file_type="pdf")

    ctx.quality_metrics = [_make_quality_metrics()]

    ctx.image_forensics_metrics = [
        {
            "page_index": 0,
            "laplacian_variance": 200.0,
            "blur_severity": 10.0,
            "noise_sigma": 3.5,
            "edge_density": 0.12,
            "illumination_std": 25.0,
            "ela_region_count": 2,
            "ela_max_difference": 40.0,
            "entropy_score": 18.0,
        },
        {
            "page_index": 1,
            "laplacian_variance": 300.0,
            "blur_severity": 5.0,
            "noise_sigma": 2.0,
            "edge_density": 0.08,
            "illumination_std": 20.0,
            "ela_region_count": 1,
            "ela_max_difference": 20.0,
            "entropy_score": 15.0,
        },
    ]

    ctx.ocr_summary = {
        "average_confidence": 0.87,
        "min_confidence": 0.42,
        "max_confidence": 0.99,
        "low_confidence_fraction": 0.08,
        "total_words": 312,
    }

    ctx.layout_summary = {
        "total_sections": 6,
        "total_fields": 14,
        "total_tables": 2,
    }

    ctx.classification_result = {
        "predicted_type": "PASSPORT",
        "confidence": 0.91,
    }

    ctx.signature_features = {
        "stroke_width_mean": 2.5,
        "stroke_width_std": 0.8,
        "contour_count": 5,
        "contour_area": 1200.0,
        "contour_perimeter": 450.0,
        "ink_density": 0.35,
        "foreground_ratio": 0.28,
        "skeleton_length": 80.0,
        "endpoint_count": 6,
        "branch_count": 4,
        "blob_count": 3,
        "aspect_ratio": 2.1,
        "solidity": 0.72,
        "eccentricity": 0.65,
        "contrast": 120.0,
        "complexity_score": 18.5,
    }

    ctx.logo_features = {
        "edge_density": 0.45,
        "resolution_quality": 0.9,
        "authenticity_score": 82.0,
        "fingerprint": {
            "orb_keypoint_count": 55,
            "orb_descriptor_density": 0.6,
            "symmetry_horizontal": 0.88,
            "symmetry_vertical": 0.91,
            "contour_count": 12,
            "contour_complexity": 3.2,
            "texture_variance": 45.0,
            "shape_circularity": 0.78,
            "shape_compactness": 0.65,
            "shape_eccentricity": 0.3,
            "aspect_ratio": 1.05,
            "solidity": 0.82,
            "hu_moments": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7],
        },
    }

    ctx.copy_move_features = {
        "keypoint_count_orb": 120,
        "keypoint_count_akaze": 95,
        "descriptor_matches": 40,
        "inlier_matches": 30,
        "average_region_size": 500.0,
        "duplicate_pair_count": 2,
        "confidence": 0.75,
        "inlier_ratio": 0.75,
    }

    ctx.evidence_category_scores = {
        "metadata": 20.0,
        "image": 60.0,
        "ocr": 15.0,
        "layout": 10.0,
        "field": 5.0,
        "signature": 70.0,
        "logo": 30.0,
        "visual": 0.0,
        "unknown": 0.0,
    }

    ctx.forgery_report = {
        "summary": {
            "total_evidence": 7,
            "highest_severity": 90.0,
            "category_counts": {
                "IMAGE": 3,
                "SIGNATURE": 2,
                "METADATA": 1,
                "OCR": 1,
                "LAYOUT": 0,
                "FIELD": 0,
                "LOGO": 0,
                "VISUAL": 0,
                "UNKNOWN": 0,
            },
            "source_counts": {},
        }
    }

    ctx.fusion_metrics = {
        "calibrated_risk": 0.65,    # present on context but NOT extracted
        "prior_risk": 0.05,         # present on context but NOT extracted
        "posterior_risk": 0.65,     # present on context but NOT extracted
        "correlation_multiplier": 1.1,
        "conflict_multiplier": 0.9,
        "calibrated_confidence": 0.8,
        "recommendation_count": 3,
        "verdict_ordinal": 2,       # present on context but NOT extracted
        "contributor_count": 5,
    }

    ctx.risk_score = 55.0           # present on context but NOT extracted

    return ctx


# ---------------------------------------------------------------------------
# Empty context
# ---------------------------------------------------------------------------

class TestFeatureExtractorEmpty:
    def test_returns_feature_vector(self, extractor, empty_context):
        vec = extractor.extract(empty_context)
        assert vec.document_id == empty_context.document_id
        assert vec.file_type == "png"

    def test_all_feature_keys_present(self, extractor, empty_context):
        vec = extractor.extract(empty_context)
        for name in FEATURE_NAMES:
            assert name in vec.features, f"Missing key: {name}"

    def test_empty_context_all_none(self, extractor, empty_context):
        vec = extractor.extract(empty_context)
        for name in FEATURE_NAMES:
            assert vec.features[name] is None, f"{name} should be None for empty context"

    def test_label_propagated(self, extractor, empty_context):
        vec = extractor.extract(empty_context, label="forged")
        assert vec.label == "forged"

    def test_no_label_is_none(self, extractor, empty_context):
        vec = extractor.extract(empty_context)
        assert vec.label is None

    def test_feature_vector_length_matches_registry(self, extractor, empty_context):
        vec = extractor.extract(empty_context)
        assert len(vec.features) == len(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Leakage prevention — all 5 excluded features
# ---------------------------------------------------------------------------

class TestLeakagePrevention:
    def test_fusion_calibrated_risk_not_exported(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert "fusion_calibrated_risk" not in vec.features

    def test_fusion_posterior_risk_not_exported(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert "fusion_posterior_risk" not in vec.features

    def test_fusion_prior_risk_not_exported(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert "fusion_prior_risk" not in vec.features

    def test_fusion_verdict_ordinal_not_exported(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert "fusion_verdict_ordinal" not in vec.features

    def test_risk_score_not_exported(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert "risk_score" not in vec.features

    def test_risk_score_still_on_context(self, extractor, full_context):
        extractor.extract(full_context)
        assert full_context.risk_score == 55.0

    def test_fusion_prior_risk_still_on_context(self, extractor, full_context):
        extractor.extract(full_context)
        assert full_context.fusion_metrics["prior_risk"] == pytest.approx(0.05)

    def test_fusion_verdict_ordinal_still_on_context(self, extractor, full_context):
        extractor.extract(full_context)
        assert full_context.fusion_metrics["verdict_ordinal"] == 2


# ---------------------------------------------------------------------------
# Image metadata
# ---------------------------------------------------------------------------

class TestImageMetadata:
    def test_width_height_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["img_width"] == pytest.approx(2480.0)
        assert vec.features["img_height"] == pytest.approx(3508.0)

    def test_aspect_ratio_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["img_aspect_ratio"] == pytest.approx(0.707)

    def test_color_channels_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["img_color_channels"] == pytest.approx(3.0)

    def test_no_quality_metrics_gives_none(self, extractor, full_context):
        full_context.quality_metrics = []
        vec = extractor.extract(full_context)
        assert vec.features["img_width"] is None
        assert vec.features["img_height"] is None


# ---------------------------------------------------------------------------
# Image forensics
# ---------------------------------------------------------------------------

class TestImageForensics:
    def test_averaged_across_pages(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["img_laplacian_variance_mean"] == pytest.approx(250.0)

    def test_page_count(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["img_page_count"] == 2.0

    def test_single_page(self, extractor, full_context):
        full_context.image_forensics_metrics = [full_context.image_forensics_metrics[0]]
        vec = extractor.extract(full_context)
        assert vec.features["img_laplacian_variance_mean"] == pytest.approx(200.0)
        assert vec.features["img_page_count"] == 1.0


# ---------------------------------------------------------------------------
# OCR features
# ---------------------------------------------------------------------------

class TestOCRFeatures:
    def test_all_ocr_features_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["ocr_average_confidence"] == pytest.approx(0.87)
        assert vec.features["ocr_min_confidence"] == pytest.approx(0.42)
        assert vec.features["ocr_max_confidence"] == pytest.approx(0.99)
        assert vec.features["ocr_low_confidence_fraction"] == pytest.approx(0.08)
        assert vec.features["ocr_total_words"] == pytest.approx(312.0)

    def test_missing_ocr_summary_gives_none(self, extractor, full_context):
        full_context.ocr_summary = None
        vec = extractor.extract(full_context)
        assert vec.features["ocr_average_confidence"] is None
        assert vec.features["ocr_total_words"] is None


# ---------------------------------------------------------------------------
# Layout features
# ---------------------------------------------------------------------------

class TestLayoutFeatures:
    def test_layout_counts_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["layout_total_sections"] == pytest.approx(6.0)
        assert vec.features["layout_total_fields"] == pytest.approx(14.0)
        assert vec.features["layout_total_tables"] == pytest.approx(2.0)

    def test_missing_layout_summary_gives_none(self, extractor, full_context):
        full_context.layout_summary = None
        vec = extractor.extract(full_context)
        assert vec.features["layout_total_sections"] is None


# ---------------------------------------------------------------------------
# Classification features
# ---------------------------------------------------------------------------

class TestClassificationFeatures:
    def test_passport_ordinal_is_5(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["classification_type_ordinal"] == pytest.approx(5.0)

    def test_confidence_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["classification_confidence"] == pytest.approx(0.91)

    def test_unknown_type_ordinal_is_0(self, extractor, full_context):
        full_context.classification_result = {"predicted_type": "UNKNOWN", "confidence": 0.3}
        vec = extractor.extract(full_context)
        assert vec.features["classification_type_ordinal"] == pytest.approx(0.0)

    def test_missing_classification_gives_none(self, extractor, full_context):
        full_context.classification_result = None
        vec = extractor.extract(full_context)
        assert vec.features["classification_type_ordinal"] is None
        assert vec.features["classification_confidence"] is None

    def test_all_document_types_have_ordinal(self, extractor, full_context):
        from app.ml.feature_registry import DOCUMENT_TYPE_ORDINAL
        for doc_type, ordinal in DOCUMENT_TYPE_ORDINAL.items():
            full_context.classification_result = {"predicted_type": doc_type, "confidence": 0.5}
            vec = extractor.extract(full_context)
            assert vec.features["classification_type_ordinal"] == pytest.approx(float(ordinal))


# ---------------------------------------------------------------------------
# Signature features
# ---------------------------------------------------------------------------

class TestSignatureFeatures:
    def test_signature_features_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["sig_complexity_score"] == pytest.approx(18.5)
        assert vec.features["sig_ink_density"] == pytest.approx(0.35)

    def test_missing_signature_gives_none(self, extractor, full_context):
        full_context.signature_features = None
        vec = extractor.extract(full_context)
        assert vec.features["sig_complexity_score"] is None


# ---------------------------------------------------------------------------
# Logo features + Hu moments
# ---------------------------------------------------------------------------

class TestLogoFeatures:
    def test_logo_scalars_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["logo_authenticity_score"] == pytest.approx(82.0)
        assert vec.features["logo_symmetry_horizontal"] == pytest.approx(0.88)

    def test_hu_moments_flattened(self, extractor, full_context):
        vec = extractor.extract(full_context)
        for i, expected in enumerate([1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7]):
            assert vec.features[f"logo_hu_{i}"] == pytest.approx(expected), f"logo_hu_{i} mismatch"

    def test_missing_hu_moments_gives_none(self, extractor, full_context):
        full_context.logo_features["fingerprint"]["hu_moments"] = None
        vec = extractor.extract(full_context)
        for i in range(7):
            assert vec.features[f"logo_hu_{i}"] is None

    def test_partial_hu_moments_pads_none(self, extractor, full_context):
        full_context.logo_features["fingerprint"]["hu_moments"] = [1.0, 2.0]
        vec = extractor.extract(full_context)
        assert vec.features["logo_hu_0"] == pytest.approx(1.0)
        assert vec.features["logo_hu_2"] is None

    def test_missing_logo_gives_none(self, extractor, full_context):
        full_context.logo_features = None
        vec = extractor.extract(full_context)
        assert vec.features["logo_authenticity_score"] is None
        assert vec.features["logo_hu_0"] is None


# ---------------------------------------------------------------------------
# Copy-move features
# ---------------------------------------------------------------------------

class TestCopyMoveFeatures:
    def test_copy_move_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.features["cm_confidence"] == pytest.approx(0.75)
        assert vec.features["cm_inlier_ratio"] == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Evidence severity scores
# ---------------------------------------------------------------------------

# Outcome-derived diagnostics are retained separately from classifier inputs
# to preserve the feature registry leakage policy.
class TestEvidenceSeverity:
    def test_severity_scores_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["ev_image"] == pytest.approx(60.0)
        assert vec.auxiliary_features["ev_signature"] == pytest.approx(70.0)


# ---------------------------------------------------------------------------
# Evidence summary
# ---------------------------------------------------------------------------

class TestEvidenceSummary:
    def test_total_count_and_highest_severity(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["evidence_total_count"] == pytest.approx(7.0)
        assert vec.auxiliary_features["evidence_highest_severity"] == pytest.approx(90.0)

    def test_category_counts_extracted(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["evidence_category_count_image"] == pytest.approx(3.0)
        assert vec.auxiliary_features["evidence_category_count_signature"] == pytest.approx(2.0)
        assert vec.auxiliary_features["evidence_category_count_layout"] == pytest.approx(0.0)

    def test_missing_forgery_report_gives_none(self, extractor, full_context):
        full_context.forgery_report = None
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["evidence_total_count"] is None
        assert vec.auxiliary_features["evidence_highest_severity"] is None
        assert vec.auxiliary_features["evidence_category_count_image"] is None


# ---------------------------------------------------------------------------
# Fusion features — only non-leakage scalars remain
# ---------------------------------------------------------------------------

class TestFusionFeatures:
    def test_exported_fusion_features(self, extractor, full_context):
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["fusion_calibrated_confidence"] == pytest.approx(0.8)
        assert vec.auxiliary_features["fusion_correlation_mult"] == pytest.approx(1.1)
        assert vec.auxiliary_features["fusion_conflict_mult"] == pytest.approx(0.9)
        assert vec.auxiliary_features["fusion_recommendation_count"] == pytest.approx(3.0)
        assert vec.auxiliary_features["fusion_contributor_count"] == pytest.approx(5.0)

    def test_missing_fusion_gives_none(self, extractor, full_context):
        full_context.fusion_metrics = None
        vec = extractor.extract(full_context)
        assert vec.auxiliary_features["fusion_calibrated_confidence"] is None
        assert vec.auxiliary_features["fusion_contributor_count"] is None


# ---------------------------------------------------------------------------
# to_row
# ---------------------------------------------------------------------------

class TestToRow:
    def test_to_row_has_all_columns(self, extractor, full_context):
        vec = extractor.extract(full_context, label="authentic")
        row = vec.to_row(FEATURE_NAMES)
        assert row["label"] == "authentic"
        for name in FEATURE_NAMES:
            assert name in row

    def test_to_row_excludes_all_leakage(self, extractor, full_context):
        vec = extractor.extract(full_context)
        row = vec.to_row(FEATURE_NAMES)
        for leaked in (
            "fusion_calibrated_risk",
            "fusion_posterior_risk",
            "fusion_prior_risk",
            "fusion_verdict_ordinal",
            "risk_score",
        ):
            assert leaked not in row, f"Leakage feature found in row: {leaked}"
