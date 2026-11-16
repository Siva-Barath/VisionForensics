"""
feature_preparer.py

Validates schema ordering, data types, finite values, and handles missing features
for ML inference in strict accordance with Phase 5 guidelines.
"""

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Medians derived exclusively from authentic training data (train_features.csv, label=0, N=660)
TRAINING_AUTHENTIC_MEDIANS: Dict[str, float] = {
    "img_width": 1080.0,
    "img_height": 1920.0,
    "img_aspect_ratio": 0.5625,
    "img_laplacian_variance_mean": 61.150787,
    "img_blur_severity_mean": 38.849213,
    "img_noise_sigma_mean": 2.965200,
    "img_edge_density_mean": 0.017692,
    "img_illumination_std_mean": 50.282839,
    "img_ela_region_count_mean": 1.0,
    "img_ela_max_difference_mean": 14.0,
    "img_entropy_score_mean": 6.359451,
    "cm_keypoint_count_akaze": 2388.0,
    "cm_descriptor_matches": 84.0,
    "cm_inlier_matches": 12.0,
    "cm_average_region_size": 0.0,
    "cm_duplicate_pair_count": 0.0,
    "cm_confidence": 0.0,
    "cm_inlier_ratio": 0.176671,
}

# Critical forensic features that account for the majority of the model's predictive power.
# If these are missing, model inference must be reported as DEGRADED or ML_UNAVAILABLE.
CRITICAL_FEATURES = {
    "img_ela_max_difference_mean",
    "img_laplacian_variance_mean",
    "img_blur_severity_mean",
}

class FeaturePreparationResult:
    def __init__(
        self,
        features_array: Optional[np.ndarray],
        features_df: Optional[pd.DataFrame],
        features_dict: Dict[str, Optional[float]],
        imputed_dict: Dict[str, float],
        completeness: float,
        warnings: List[str],
        is_critical_missing: bool,
    ):
        self.features_array = features_array
        self.features_df = features_df
        self.features_dict = features_dict
        self.imputed_dict = imputed_dict
        self.completeness = completeness
        self.warnings = warnings
        self.is_critical_missing = is_critical_missing


class FeaturePreparer:
    """Validates and prepares raw feature dictionaries for frozen model inference."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.active_features: List[str] = self._load_schema()

    def _load_schema(self) -> List[str]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Feature schema not found at {self.schema_path}")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        if len(features) != 18:
            raise ValueError(f"Expected 18 features in active schema, found {len(features)}")
        return features

    def prepare(self, raw_features: Dict[str, Any]) -> FeaturePreparationResult:
        """
        Validates the 18 active features, detects missing/invalid values,
        applies training-baseline imputation only when permitted, and formats
        the numpy array in the exact schema order.
        """
        prepared_dict: Dict[str, Optional[float]] = {}
        imputed_dict: Dict[str, float] = {}
        warnings: List[str] = []
        ordered_values: List[float] = []
        missing_count = 0
        critical_missing = False

        for feat in self.active_features:
            val = raw_features.get(feat, None)

            # Check for missing, None, NaN, or Infinite
            is_invalid = False
            if val is None:
                is_invalid = True
            else:
                try:
                    f_val = float(val)
                    if math.isnan(f_val) or math.isinf(f_val):
                        is_invalid = True
                    else:
                        val = f_val
                except (ValueError, TypeError):
                    is_invalid = True

            if is_invalid:
                missing_count += 1
                if feat in CRITICAL_FEATURES:
                    critical_missing = True
                    warnings.append(
                        f"Critical forensic feature '{feat}' is missing or invalid. Reliable inference compromised."
                    )
                else:
                    warnings.append(
                        f"Feature '{feat}' is missing or invalid. Using authentic training baseline."
                    )

                # Fallback to training baseline median
                fallback = TRAINING_AUTHENTIC_MEDIANS.get(feat, 0.0)
                imputed_dict[feat] = fallback
                prepared_dict[feat] = fallback
                ordered_values.append(fallback)
            else:
                prepared_dict[feat] = float(val)
                ordered_values.append(float(val))

        completeness = float((len(self.active_features) - missing_count) / len(self.active_features))
        features_array = np.array(ordered_values, dtype=np.float64).reshape(1, -1)
        features_df = pd.DataFrame([prepared_dict], columns=self.active_features)

        return FeaturePreparationResult(
            features_array=features_array,
            features_df=features_df,
            features_dict=prepared_dict,
            imputed_dict=imputed_dict,
            completeness=completeness,
            warnings=warnings,
            is_critical_missing=critical_missing,
        )
