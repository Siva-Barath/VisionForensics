"""
inference_service.py — Core implementation of MLInferenceService for VisionForensics AI.
Loads the frozen Random Forest pipeline safely, validates features, and computes calibrated predictions.
"""

import time
import logging
import hashlib
import io
import json
from pathlib import Path
from typing import Dict, Any, Optional

import joblib
import numpy as np

from app.pipeline.context import AnalysisContext
from app.ml.feature_extractor import FeatureExtractor
from .models import (
    MLPredictionResult,
    RiskTier,
    InferenceStatus,
    ForensicLimitationNotice,
)
from .feature_preparer import (
    FeaturePreparer,
    FeaturePreparationResult,
    TRAINING_AUTHENTIC_MEDIANS,
    CRITICAL_FEATURES,
)

logger = logging.getLogger(__name__)

# Default artifact location
_APP_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_ARTIFACTS_DIR = _APP_ROOT / "ml" / "artifacts"
FROZEN_MODEL_SHA256 = "f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280"
FROZEN_SCHEMA_SHA256 = "eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc"

# Authoritative Operational Risk Descriptions (as approved in Phase 5 specifications)
RISK_DESCRIPTIONS = {
    RiskTier.LOW_RISK: "Preliminary screening indicates relatively low forgery risk. This is not a guarantee of authenticity.",
    RiskTier.SUSPICIOUS: "Document requires manual forensic investigation.",
    RiskTier.HIGH_RISK: "Strong forgery indicators detected. Priority forensic review is recommended.",
    RiskTier.UNKNOWN: "Risk classification could not be determined due to missing model or critical feature extraction failure.",
}

class MLInferenceService:
    """
    Thread-safe, singleton-capable service for frozen ML model inference.
    Executes the 18-feature Random Forest model at operational threshold T=0.40.
    """

    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or _DEFAULT_ARTIFACTS_DIR
        self.model_path = self.artifacts_dir / "random_forest.joblib"
        self.schema_path = self.artifacts_dir / "active_feature_schema.json"
        
        self.model = None
        self.feature_preparer: Optional[FeaturePreparer] = None
        self.feature_extractor = FeatureExtractor()
        self.is_loaded = False
        self.load_error: Optional[str] = None
        
        # Load model and schema on instantiation
        self.load_artifacts()

    def load_artifacts(self) -> bool:
        """Loads and verifies frozen model and schema artifacts. Returns True on success."""
        try:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Frozen model artifact missing at {self.model_path}")
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Feature schema missing at {self.schema_path}")

            # Verify executable pickle bytes before deserialization. Load exactly
            # the verified bytes so a file replacement cannot race the check.
            model_bytes = self.model_path.read_bytes()
            schema_bytes = self.schema_path.read_bytes()
            if hashlib.sha256(model_bytes).hexdigest() != FROZEN_MODEL_SHA256:
                raise ValueError("Frozen model SHA-256 integrity check failed")
            if hashlib.sha256(schema_bytes).hexdigest() != FROZEN_SCHEMA_SHA256:
                raise ValueError("Frozen feature schema SHA-256 integrity check failed")
            expected_features = json.loads(schema_bytes)["features"]
            self.feature_preparer = FeaturePreparer(self.schema_path)
            if self.feature_preparer.active_features != expected_features:
                raise ValueError("Feature schema changed during loading")
            self.model = joblib.load(io.BytesIO(model_bytes))

            # Integrity check: model must implement predict_proba
            if not hasattr(self.model, "predict_proba"):
                raise TypeError(f"Loaded object from {self.model_path} does not implement predict_proba")
            if list(getattr(self.model, "feature_names_in_", [])) != expected_features:
                raise ValueError("Frozen model feature names/order do not match the verified schema")
            if getattr(self.model, "n_features_in_", None) != 18:
                raise ValueError("Frozen model must accept exactly 18 features")
            if list(getattr(self.model, "classes_", [])) != [0, 1]:
                raise ValueError("Frozen model class ordering must be [0, 1]")

            self.is_loaded = True
            self.load_error = None
            logger.info("MLInferenceService successfully loaded frozen Random Forest pipeline.")
            return True
        except Exception as e:
            self.model = None
            self.feature_preparer = None
            self.is_loaded = False
            self.load_error = str(e)
            logger.error("Failed to load frozen ML model artifacts: %s", self.load_error)
            return False

    def predict_from_features(
        self,
        features_dict: Dict[str, Any],
        operational_threshold: float = 0.40,
        alternative_threshold: float = 0.50,
    ) -> MLPredictionResult:
        """
        Executes model inference directly on an extracted feature dictionary.
        Enables standalone verification, unit testing, and pipeline decoupling.
        """
        start_time = time.perf_counter()

        # 1. Check model availability
        if not self.is_loaded or self.model is None:
            duration = (time.perf_counter() - start_time) * 1000
            return MLPredictionResult(
                status=InferenceStatus.ML_UNAVAILABLE,
                operational_threshold=operational_threshold,
                alternative_threshold=alternative_threshold,
                risk_tier=RiskTier.UNKNOWN,
                risk_description=RISK_DESCRIPTIONS[RiskTier.UNKNOWN],
                warnings=[f"ML inference model is unavailable: {self.load_error or 'Artifacts not loaded'}"],
                limitations=self._build_limitations(0.0),
                inference_duration_ms=duration,
            )

        # 2. Prepare, validate, and order features
        prep_res: FeaturePreparationResult = self.feature_preparer.prepare(features_dict)

        # Check for critical feature failure
        if prep_res.is_critical_missing:
            # If all 3 critical features are missing, complete forensic inference is impossible
            missing_critical_count = sum(1 for f in CRITICAL_FEATURES if f in prep_res.imputed_dict)
            if missing_critical_count >= 2:
                duration = (time.perf_counter() - start_time) * 1000
                return MLPredictionResult(
                    status=InferenceStatus.ML_UNAVAILABLE,
                    operational_threshold=operational_threshold,
                    alternative_threshold=alternative_threshold,
                    risk_tier=RiskTier.UNKNOWN,
                    risk_description=RISK_DESCRIPTIONS[RiskTier.UNKNOWN],
                    feature_completeness=prep_res.completeness,
                    feature_vector=prep_res.features_dict,
                    imputed_features=prep_res.imputed_dict,
                    warnings=prep_res.warnings + ["Multiple critical forensic features are missing. Prediction aborted."],
                    limitations=self._build_limitations(0.0),
                    inference_duration_ms=duration,
                )
            status = InferenceStatus.DEGRADED
        elif prep_res.completeness < 1.0:
            status = InferenceStatus.DEGRADED
        else:
            status = InferenceStatus.SUCCESS

        # 3. Model inference
        try:
            # Predict probabilities using named DataFrame to match model schema
            input_data = prep_res.features_df if prep_res.features_df is not None else prep_res.features_array
            prob_forged = float(self.model.predict_proba(input_data)[0, 1])
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error("Scikit-learn model inference failed: %s", str(e))
            return MLPredictionResult(
                status=InferenceStatus.ML_UNAVAILABLE,
                operational_threshold=operational_threshold,
                alternative_threshold=alternative_threshold,
                risk_tier=RiskTier.UNKNOWN,
                risk_description=RISK_DESCRIPTIONS[RiskTier.UNKNOWN],
                warnings=prep_res.warnings + [f"Inference execution failed: {str(e)}"],
                limitations=self._build_limitations(0.0),
                inference_duration_ms=duration,
            )

        # 4. Classify predictions at operational and alternative thresholds
        predicted_class = "FORGED" if prob_forged >= operational_threshold else "AUTHENTIC"
        predicted_class_alt = "FORGED" if prob_forged >= alternative_threshold else "AUTHENTIC"

        # 5. Determine operational risk tier
        if prob_forged < 0.30:
            risk_tier = RiskTier.LOW_RISK
        elif prob_forged < 0.55:
            risk_tier = RiskTier.SUSPICIOUS
        else:
            risk_tier = RiskTier.HIGH_RISK

        risk_description = RISK_DESCRIPTIONS[risk_tier]

        # 6. Extract top contributing features (based on deviation from authentic medians)
        top_contributors = self._compute_top_contributors(prep_res.features_dict)

        # 7. Build limitations and disclaimers
        limitations = self._build_limitations(prob_forged)

        duration = (time.perf_counter() - start_time) * 1000

        return MLPredictionResult(
            status=status,
            predicted_class=predicted_class,
            forgery_probability=round(prob_forged, 4),
            operational_threshold=operational_threshold,
            alternative_threshold=alternative_threshold,
            predicted_class_alt=predicted_class_alt,
            risk_tier=risk_tier,
            risk_description=risk_description,
            model_name="RandomForestClassifier",
            model_version="1.0.0-rf-midv500-18feat",
            feature_completeness=round(prep_res.completeness, 3),
            feature_vector=prep_res.features_dict,
            imputed_features=prep_res.imputed_dict,
            top_contributing_features=top_contributors,
            warnings=prep_res.warnings,
            limitations=limitations,
            inference_duration_ms=round(duration, 2),
        )

    def predict(
        self,
        context: AnalysisContext,
        operational_threshold: float = 0.40,
        alternative_threshold: float = 0.50,
    ) -> MLPredictionResult:
        """
        Full pipeline entry point: extracts features from AnalysisContext and executes inference.
        """
        # Extract features using existing FeatureExtractor
        vec = self.feature_extractor.extract(context)
        raw_features = vec.features if hasattr(vec, "features") else {}
        return self.predict_from_features(
            raw_features,
            operational_threshold=operational_threshold,
            alternative_threshold=alternative_threshold,
        )

    def predict_page(
        self,
        context: AnalysisContext,
        page_index: int,
        operational_threshold: float = 0.40,
        alternative_threshold: float = 0.50,
    ) -> MLPredictionResult:
        """
        Executes ML inference on a single page of a document without cross-page dilution (REM-01).
        """
        vec = self.feature_extractor.extract_page(context, page_index=page_index)
        raw_features = vec.features if hasattr(vec, "features") else {}
        return self.predict_from_features(
            raw_features,
            operational_threshold=operational_threshold,
            alternative_threshold=alternative_threshold,
        )

    def _compute_top_contributors(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        """Identifies key features showing elevated anomaly signatures compared to authentic baseline."""
        contributors = {}
        # 1. ELA peak difference
        ela_diff = feature_dict.get("img_ela_max_difference_mean")
        if ela_diff is not None:
            contributors["img_ela_max_difference_mean"] = round(float(ela_diff), 2)

        # 2. Laplacian variance
        lap = feature_dict.get("img_laplacian_variance_mean")
        if lap is not None:
            contributors["img_laplacian_variance_mean"] = round(float(lap), 2)

        # 3. Blur severity
        blur = feature_dict.get("img_blur_severity_mean")
        if blur is not None:
            contributors["img_blur_severity_mean"] = round(float(blur), 2)

        # 4. Copy-move matches
        cm_matches = feature_dict.get("cm_inlier_matches")
        if cm_matches is not None and float(cm_matches) > 15.0:
            contributors["cm_inlier_matches"] = round(float(cm_matches), 1)

        return contributors

    def _build_limitations(self, probability: float) -> list[ForensicLimitationNotice]:
        """Assembles required forensic decision support disclaimers."""
        notices = [
            ForensicLimitationNotice(
                code="DECISION_SUPPORT_NOTICE",
                severity="INFO",
                message="Predictions must be evaluated as forensic decision support, not definitive legal proof of fraud.",
            ),
            ForensicLimitationNotice(
                code="COPY_MOVE_SENSITIVITY",
                severity="WARNING",
                message="Intra-document copy-move clones sharing compression history exhibit lower recall (~43%-54%). Manual review recommended for textureless duplicate regions.",
            ),
            ForensicLimitationNotice(
                code="SYNTHETIC_DATASET_SCOPE",
                severity="INFO",
                message="Model was evaluated on MIDV-500 specimens and synthetic localized forgeries. Real-world artifacts may vary.",
            ),
        ]
        if probability >= 0.55:
            notices.append(
                ForensicLimitationNotice(
                    code="HIGH_RISK_CALIBRATION_NOTICE",
                    severity="INFO",
                    message="The T=0.55 high-risk boundary is provisional; precision and false-positive statistics for T>=0.55 are validation-only results.",
                )
            )
        return notices
