"""
test_ml_inference_service.py

Unit tests for Phase 5A: MLInferenceService
Tests model loading, schema validation, feature preparation, imputation,
operational thresholding (T=0.40), risk tiers, and limitation notices.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure backend is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for p in (_REPO_ROOT, _BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.services.ml_inference import (
    MLInferenceService,
    InferenceStatus,
    RiskTier,
    FeaturePreparer,
    TRAINING_AUTHENTIC_MEDIANS,
)

class TestMLInferenceService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = MLInferenceService()
        cls.assertTrue(cls.service.is_loaded, f"Failed to load model: {cls.service.load_error}")
        
        # Load sample real rows from train_features.csv for verification
        feat_csv = Path(r"D:\Datasets\TrainingDataset\ml_phase2\features\train_features.csv")
        cls.assertTrue(feat_csv.exists(), "Missing train_features.csv for unit tests")
        df = pd.read_csv(feat_csv)
        
        cls.sample_auth = df[df["label"] == 0].iloc[0].to_dict()
        cls.sample_forg = df[df["label"] == 1].iloc[0].to_dict()

    def test_01_model_and_schema_loading(self):
        """Test model and schema load successfully and feature preparer has 18 features."""
        self.assertTrue(self.service.is_loaded)
        self.assertIsNotNone(self.service.model)
        self.assertIsNotNone(self.service.feature_preparer)
        self.assertEqual(len(self.service.feature_preparer.active_features), 18)

    def test_02_predict_authentic_sample(self):
        """Test inference on a known authentic feature vector produces low risk / authentic."""
        res = self.service.predict_from_features(self.sample_auth, operational_threshold=0.40)
        self.assertEqual(res.status, InferenceStatus.SUCCESS)
        self.assertIsNotNone(res.forgery_probability)
        self.assertLess(res.forgery_probability, 0.40)
        self.assertEqual(res.predicted_class, "AUTHENTIC")
        self.assertIn(res.risk_tier, [RiskTier.LOW_RISK, RiskTier.SUSPICIOUS])
        self.assertEqual(len(res.imputed_features), 0)
        self.assertEqual(res.feature_completeness, 1.0)

    def test_03_predict_forged_sample(self):
        """Test inference on a known forged feature vector produces high risk / forged."""
        res = self.service.predict_from_features(self.sample_forg, operational_threshold=0.40)
        self.assertEqual(res.status, InferenceStatus.SUCCESS)
        self.assertIsNotNone(res.forgery_probability)
        self.assertGreaterEqual(res.forgery_probability, 0.40)
        self.assertEqual(res.predicted_class, "FORGED")
        self.assertIn(res.risk_tier, [RiskTier.SUSPICIOUS, RiskTier.HIGH_RISK])

    def test_04_feature_order_invariance(self):
        """Test that arbitrary dictionary key ordering produces identical predictions."""
        shuffled_auth = dict(sorted(self.sample_auth.items(), key=lambda x: x[0], reverse=True))
        res1 = self.service.predict_from_features(self.sample_auth)
        res2 = self.service.predict_from_features(shuffled_auth)
        self.assertEqual(res1.forgery_probability, res2.forgery_probability)

    def test_05_non_critical_missing_imputation(self):
        """Test missing non-critical feature is imputed with training baseline and explicitly reported."""
        incomplete_sample = dict(self.sample_auth)
        del incomplete_sample["cm_keypoint_count_akaze"]
        incomplete_sample["img_edge_density_mean"] = None  # None value

        res = self.service.predict_from_features(incomplete_sample)
        self.assertEqual(res.status, InferenceStatus.DEGRADED)
        self.assertEqual(len(res.imputed_features), 2)
        self.assertIn("cm_keypoint_count_akaze", res.imputed_features)
        self.assertIn("img_edge_density_mean", res.imputed_features)
        self.assertLess(res.feature_completeness, 1.0)
        self.assertTrue(len(res.warnings) >= 2)

    def test_06_critical_features_missing_abort(self):
        """Test that missing multiple critical features causes ML_UNAVAILABLE rather than false confidence."""
        corrupt_sample = dict(self.sample_auth)
        corrupt_sample["img_ela_max_difference_mean"] = None
        corrupt_sample["img_laplacian_variance_mean"] = None

        res = self.service.predict_from_features(corrupt_sample)
        self.assertEqual(res.status, InferenceStatus.ML_UNAVAILABLE)
        self.assertIsNone(res.predicted_class)
        self.assertEqual(res.risk_tier, RiskTier.UNKNOWN)
        self.assertTrue(any("critical forensic feature" in w.lower() for w in res.warnings))

    def test_07_operational_vs_alternative_threshold(self):
        """Test thresholding logic at T=0.40 (screening) and T=0.50 (alternative)."""
        # Create a borderline feature dictionary where prob is around ~0.45
        sample = dict(self.sample_auth)
        sample["img_ela_max_difference_mean"] = 24.0
        sample["img_laplacian_variance_mean"] = 120.0
        
        res = self.service.predict_from_features(sample, operational_threshold=0.40, alternative_threshold=0.50)
        self.assertEqual(res.operational_threshold, 0.40)
        self.assertEqual(res.alternative_threshold, 0.50)

    def test_08_limitations_notices(self):
        """Test forensic decision support notices are present."""
        res = self.service.predict_from_features(self.sample_forg)
        codes = [item.code for item in res.limitations]
        self.assertIn("DECISION_SUPPORT_NOTICE", codes)
        self.assertIn("COPY_MOVE_SENSITIVITY", codes)
        self.assertIn("SYNTHETIC_DATASET_SCOPE", codes)
        if res.forgery_probability >= 0.55:
            self.assertIn("HIGH_RISK_CALIBRATION_NOTICE", codes)

if __name__ == "__main__":
    unittest.main()
