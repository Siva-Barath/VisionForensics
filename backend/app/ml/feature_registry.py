"""
FeatureRegistry — single source of truth for every feature name and its
extraction path from AnalysisContext.

Each entry is a (feature_name, extractor_key) tuple where extractor_key
maps to a method on FeatureExtractor.  The registry drives both extraction
order and CSV column order so they are always in sync.

Leakage policy
--------------
The following are intentionally excluded from the exported feature set
to prevent the ML model from learning the rule engine's own output:
  - fusion_calibrated_risk   (final Bayesian posterior)
  - fusion_posterior_risk    (final Bayesian posterior)
  - fusion_prior_risk        (fixed constant 0.05 — zero variance)
  - fusion_verdict_ordinal   (final verdict decision)
  - risk_score               (final weighted risk decision)
They remain on AnalysisContext for post-inference evaluation only.
"""
from __future__ import annotations
from typing import NamedTuple


class FeatureDef(NamedTuple):
    name: str    # CSV column name
    group: str   # logical group for documentation / ablation


# ---------------------------------------------------------------------------
# Image metadata — from context.quality_metrics[0] (first page dimensions).
# ---------------------------------------------------------------------------
IMAGE_METADATA_FEATURES: list[FeatureDef] = [
    FeatureDef("img_width",          "image_metadata"),
    FeatureDef("img_height",         "image_metadata"),
    FeatureDef("img_aspect_ratio",   "image_metadata"),
    FeatureDef("img_color_channels", "image_metadata"),
]

# ---------------------------------------------------------------------------
# Image forensics — one entry per scalar exposed by ImageArtifactDetector.
# When multiple pages exist the extractor averages across pages.
# ---------------------------------------------------------------------------
IMAGE_FORENSICS_FEATURES: list[FeatureDef] = [
    FeatureDef("img_laplacian_variance_mean", "image_forensics"),
    FeatureDef("img_blur_severity_mean",      "image_forensics"),
    FeatureDef("img_noise_sigma_mean",        "image_forensics"),
    FeatureDef("img_edge_density_mean",       "image_forensics"),
    FeatureDef("img_illumination_std_mean",   "image_forensics"),
    FeatureDef("img_ela_region_count_mean",   "image_forensics"),
    FeatureDef("img_ela_max_difference_mean", "image_forensics"),
    FeatureDef("img_entropy_score_mean",      "image_forensics"),
    FeatureDef("img_page_count",              "image_forensics"),
]

# ---------------------------------------------------------------------------
# OCR features — from context.ocr_summary (serialised OCRSummary).
# ---------------------------------------------------------------------------
OCR_FEATURES: list[FeatureDef] = [
    FeatureDef("ocr_average_confidence",      "ocr"),
    FeatureDef("ocr_min_confidence",          "ocr"),
    FeatureDef("ocr_max_confidence",          "ocr"),
    FeatureDef("ocr_low_confidence_fraction", "ocr"),
    FeatureDef("ocr_total_words",             "ocr"),
]

# ---------------------------------------------------------------------------
# Layout features — from context.layout_summary (serialised LayoutSummary).
# ---------------------------------------------------------------------------
LAYOUT_FEATURES: list[FeatureDef] = [
    FeatureDef("layout_total_sections", "layout"),
    FeatureDef("layout_total_fields",   "layout"),
    FeatureDef("layout_total_tables",   "layout"),
]

# ---------------------------------------------------------------------------
# Document classification — from context.classification_result.
# classification_type_ordinal uses the deterministic DocumentType enum order:
#   UNKNOWN=0, MARKSHEET=1, DEGREE_CERTIFICATE=2, TRANSCRIPT=3,
#   ID_CARD=4, PASSPORT=5, INVOICE=6, RECEIPT=7
# ---------------------------------------------------------------------------
CLASSIFICATION_FEATURES: list[FeatureDef] = [
    FeatureDef("classification_type_ordinal", "classification"),
    FeatureDef("classification_confidence",   "classification"),
]

# ---------------------------------------------------------------------------
# Signature features — from SignatureFeatures dataclass (first region).
# ---------------------------------------------------------------------------
SIGNATURE_FEATURES: list[FeatureDef] = [
    FeatureDef("sig_stroke_width_mean",  "signature"),
    FeatureDef("sig_stroke_width_std",   "signature"),
    FeatureDef("sig_contour_count",      "signature"),
    FeatureDef("sig_contour_area",       "signature"),
    FeatureDef("sig_contour_perimeter",  "signature"),
    FeatureDef("sig_ink_density",        "signature"),
    FeatureDef("sig_foreground_ratio",   "signature"),
    FeatureDef("sig_skeleton_length",    "signature"),
    FeatureDef("sig_endpoint_count",     "signature"),
    FeatureDef("sig_branch_count",       "signature"),
    FeatureDef("sig_blob_count",         "signature"),
    FeatureDef("sig_aspect_ratio",       "signature"),
    FeatureDef("sig_solidity",           "signature"),
    FeatureDef("sig_eccentricity",       "signature"),
    FeatureDef("sig_contrast",           "signature"),
    FeatureDef("sig_complexity_score",   "signature"),
]

# ---------------------------------------------------------------------------
# Logo features — from LogoFeatures dataclass (first region).
# Hu moments are flattened from LogoFingerprint.hu_moments list[float].
# ---------------------------------------------------------------------------
LOGO_FEATURES: list[FeatureDef] = [
    FeatureDef("logo_edge_density",           "logo"),
    FeatureDef("logo_resolution_quality",     "logo"),
    FeatureDef("logo_authenticity_score",     "logo"),
    FeatureDef("logo_orb_keypoint_count",     "logo"),
    FeatureDef("logo_orb_descriptor_density", "logo"),
    FeatureDef("logo_symmetry_horizontal",    "logo"),
    FeatureDef("logo_symmetry_vertical",      "logo"),
    FeatureDef("logo_contour_count",          "logo"),
    FeatureDef("logo_contour_complexity",     "logo"),
    FeatureDef("logo_texture_variance",       "logo"),
    FeatureDef("logo_shape_circularity",      "logo"),
    FeatureDef("logo_shape_compactness",      "logo"),
    FeatureDef("logo_shape_eccentricity",     "logo"),
    FeatureDef("logo_aspect_ratio",           "logo"),
    FeatureDef("logo_solidity",               "logo"),
    FeatureDef("logo_hu_0",                   "logo"),
    FeatureDef("logo_hu_1",                   "logo"),
    FeatureDef("logo_hu_2",                   "logo"),
    FeatureDef("logo_hu_3",                   "logo"),
    FeatureDef("logo_hu_4",                   "logo"),
    FeatureDef("logo_hu_5",                   "logo"),
    FeatureDef("logo_hu_6",                   "logo"),
]

# ---------------------------------------------------------------------------
# Copy-move features — from CopyMoveFeatures serialised dict.
# ---------------------------------------------------------------------------
COPY_MOVE_FEATURES: list[FeatureDef] = [
    FeatureDef("cm_keypoint_count_orb",   "copy_move"),
    FeatureDef("cm_keypoint_count_akaze", "copy_move"),
    FeatureDef("cm_descriptor_matches",   "copy_move"),
    FeatureDef("cm_inlier_matches",       "copy_move"),
    FeatureDef("cm_average_region_size",  "copy_move"),
    FeatureDef("cm_duplicate_pair_count", "copy_move"),
    FeatureDef("cm_confidence",           "copy_move"),
    FeatureDef("cm_inlier_ratio",         "copy_move"),
]

# ---------------------------------------------------------------------------
# Evidence category severity scores — max severity per EvidenceCategory,
# set by RiskEstimator.last_max_severity → ForgeryService → context.
# ---------------------------------------------------------------------------
EVIDENCE_SEVERITY_FEATURES: list[FeatureDef] = [
    FeatureDef("ev_metadata",  "evidence_severity"),
    FeatureDef("ev_image",     "evidence_severity"),
    FeatureDef("ev_ocr",       "evidence_severity"),
    FeatureDef("ev_layout",    "evidence_severity"),
    FeatureDef("ev_field",     "evidence_severity"),
    FeatureDef("ev_signature", "evidence_severity"),
    FeatureDef("ev_logo",      "evidence_severity"),
    FeatureDef("ev_visual",    "evidence_severity"),
    FeatureDef("ev_unknown",   "evidence_severity"),
]

# ---------------------------------------------------------------------------
# Evidence summary — aggregated counts and peak severity from EvidenceSummary
# inside context.forgery_report["summary"].
# ---------------------------------------------------------------------------
EVIDENCE_SUMMARY_FEATURES: list[FeatureDef] = [
    FeatureDef("evidence_total_count",              "evidence_summary"),
    FeatureDef("evidence_highest_severity",         "evidence_summary"),
    FeatureDef("evidence_category_count_metadata",  "evidence_summary"),
    FeatureDef("evidence_category_count_image",     "evidence_summary"),
    FeatureDef("evidence_category_count_ocr",       "evidence_summary"),
    FeatureDef("evidence_category_count_layout",    "evidence_summary"),
    FeatureDef("evidence_category_count_field",     "evidence_summary"),
    FeatureDef("evidence_category_count_signature", "evidence_summary"),
    FeatureDef("evidence_category_count_logo",      "evidence_summary"),
    FeatureDef("evidence_category_count_visual",    "evidence_summary"),
    FeatureDef("evidence_category_count_unknown",   "evidence_summary"),
]

# ---------------------------------------------------------------------------
# Fusion metrics — process scalars from EvidenceFusionService.
# EXCLUDED (leakage / constant):
#   fusion_calibrated_risk  — final Bayesian posterior decision
#   fusion_posterior_risk   — final Bayesian posterior decision
#   fusion_prior_risk       — fixed constant 0.05, zero variance
#   fusion_verdict_ordinal  — final verdict decision
# ---------------------------------------------------------------------------
FUSION_FEATURES: list[FeatureDef] = [
    FeatureDef("fusion_correlation_mult",      "fusion"),
    FeatureDef("fusion_conflict_mult",         "fusion"),
    FeatureDef("fusion_calibrated_confidence", "fusion"),
    FeatureDef("fusion_recommendation_count",  "fusion"),
    FeatureDef("fusion_contributor_count",     "fusion"),
]

# ---------------------------------------------------------------------------
# Master ordered registry (drives CSV column order).
# Excluded leakage features: fusion_calibrated_risk, fusion_posterior_risk,
# fusion_prior_risk, fusion_verdict_ordinal, risk_score.
# ---------------------------------------------------------------------------
ALL_FEATURES: list[FeatureDef] = (
    IMAGE_METADATA_FEATURES
    + IMAGE_FORENSICS_FEATURES
    + OCR_FEATURES
    + LAYOUT_FEATURES
    + CLASSIFICATION_FEATURES
    + SIGNATURE_FEATURES
    + LOGO_FEATURES
    + COPY_MOVE_FEATURES
)

FEATURE_NAMES: list[str] = [f.name for f in ALL_FEATURES]

# Deterministic DocumentType → ordinal mapping (must stay stable across runs).
DOCUMENT_TYPE_ORDINAL: dict[str, int] = {
    "UNKNOWN":            0,
    "MARKSHEET":          1,
    "DEGREE_CERTIFICATE": 2,
    "TRANSCRIPT":         3,
    "ID_CARD":            4,
    "PASSPORT":           5,
    "INVOICE":            6,
    "RECEIPT":            7,
}
