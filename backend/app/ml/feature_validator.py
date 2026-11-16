"""
FeatureValidator — validates a FeatureVector before it is written to the dataset.

Checks (Part 6):
1.  No duplicate feature names in the registry.
2.  No missing feature names (all FEATURE_NAMES keys must be present).
3.  No NaN values.
4.  No Infinity values.
5.  Numeric type consistency (all non-None values must be float-compatible).
6.  Leakage features are absent from the vector.
7.  Feature vector length equals registry length.
8.  Bounded features stay within declared ranges (warning, not error).
9.  Warn if all image-forensics features are None.
10. Warn if all OCR features are None.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.ml.feature_registry import FEATURE_NAMES, DOCUMENT_TYPE_ORDINAL
from app.ml.feature_vector import FeatureVector

# All features that must never appear in an exported FeatureVector.
_LEAKAGE_FEATURES: frozenset[str] = frozenset({
    "fusion_calibrated_risk",
    "fusion_posterior_risk",
    "fusion_prior_risk",
    "fusion_verdict_ordinal",
    "risk_score",
})

# Features with known [min, max] bounds — violations produce warnings, not errors.
_BOUNDS: dict[str, tuple[float, float]] = {
    "img_aspect_ratio":                (0.0, 20.0),
    "img_color_channels":              (1.0, 4.0),
    "img_blur_severity_mean":          (0.0, 100.0),
    "img_edge_density_mean":           (0.0, 1.0),
    "ocr_average_confidence":          (0.0, 1.0),
    "ocr_min_confidence":              (0.0, 1.0),
    "ocr_max_confidence":              (0.0, 1.0),
    "ocr_low_confidence_fraction":     (0.0, 1.0),
    "classification_type_ordinal":     (0.0, float(max(DOCUMENT_TYPE_ORDINAL.values()))),
    "classification_confidence":       (0.0, 1.0),
    "sig_ink_density":                 (0.0, 1.0),
    "sig_foreground_ratio":            (0.0, 1.0),
    "sig_solidity":                    (0.0, 1.0),
    "logo_authenticity_score":         (0.0, 100.0),
    "logo_edge_density":               (0.0, 1.0),
    "cm_confidence":                   (0.0, 1.0),
    "cm_inlier_ratio":                 (0.0, 1.0),
    "ev_metadata":                     (0.0, 100.0),
    "ev_image":                        (0.0, 100.0),
    "ev_ocr":                          (0.0, 100.0),
    "ev_layout":                       (0.0, 100.0),
    "ev_field":                        (0.0, 100.0),
    "ev_signature":                    (0.0, 100.0),
    "ev_logo":                         (0.0, 100.0),
    "ev_visual":                       (0.0, 100.0),
    "ev_unknown":                      (0.0, 100.0),
    "evidence_highest_severity":       (0.0, 100.0),
    "fusion_calibrated_confidence":    (0.0, 1.0),
    "fusion_correlation_mult":         (0.5, 2.0),
    "fusion_conflict_mult":            (0.0, 2.0),
}

# Pre-compute registry duplicate check once at import time.
_REGISTRY_DUPLICATE_NAMES: list[str] = [
    name for name in FEATURE_NAMES
    if FEATURE_NAMES.count(name) > 1
]

_IMG_FORENSICS_KEYS: list[str] = [
    k for k in FEATURE_NAMES
    if k.startswith("img_") and k not in {"img_width", "img_height", "img_aspect_ratio", "img_color_channels"}
]
_OCR_KEYS: list[str] = [k for k in FEATURE_NAMES if k.startswith("ocr_")]


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.valid = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


class FeatureValidator:
    def validate(self, vector: FeatureVector) -> ValidationResult:
        result = ValidationResult()

        # Check 1 — no duplicate names in registry (structural, not per-vector)
        if _REGISTRY_DUPLICATE_NAMES:
            result.fail(f"Registry contains duplicate feature names: {_REGISTRY_DUPLICATE_NAMES}")

        # Check 2 — vector length equals registry length
        expected_len = len(FEATURE_NAMES)
        actual_len = len(vector.features)
        if actual_len != expected_len:
            result.fail(
                f"Feature vector length mismatch: expected {expected_len}, got {actual_len}"
            )

        # Check 3 — no missing feature names
        for name in FEATURE_NAMES:
            if name not in vector.features:
                result.fail(f"Missing feature key: {name}")

        # Check 4 — leakage features absent
        for leaked in _LEAKAGE_FEATURES:
            if leaked in vector.features:
                result.fail(f"Leakage feature present in vector: {leaked}")

        # Check 5 — NaN / Inf / type consistency
        for name, value in vector.features.items():
            if value is None:
                continue
            # Type consistency: must be numeric
            if not isinstance(value, (int, float)):
                result.fail(f"Non-numeric value for {name}: {type(value).__name__}={value!r}")
                continue
            if math.isnan(value):
                result.fail(f"NaN value for feature: {name}")
                continue
            if math.isinf(value):
                result.fail(f"Infinity value for feature: {name} = {value}")
                continue
            # Check 6 — range bounds (warning only)
            if name in _BOUNDS:
                lo, hi = _BOUNDS[name]
                if not (lo <= value <= hi):
                    result.warn(f"{name}={value:.4f} outside expected range [{lo}, {hi}]")

        # Check 7 — warn if all image forensics are None
        if _IMG_FORENSICS_KEYS and all(vector.features.get(k) is None for k in _IMG_FORENSICS_KEYS):
            result.warn("All image forensics features are None — ImageArtifactDetector may not have run.")

        # Check 8 — warn if all OCR features are None
        if _OCR_KEYS and all(vector.features.get(k) is None for k in _OCR_KEYS):
            result.warn("All OCR features are None — OCRStage may not have run.")

        return result
