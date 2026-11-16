"""
test_ml_inference_stage.py

Unit tests for Phase 5B: MLInferenceStage
Tests pipeline stage execution, context updates, and non-fatal fallback.
"""

import sys
import asyncio
import unittest
from pathlib import Path

# Ensure backend is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for p in (_REPO_ROOT, _BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.pipeline.context import AnalysisContext
from app.pipeline.stages.ml_inference_stage import MLInferenceStage
from app.services.ml_inference import MLInferenceService, InferenceStatus

class TestMLInferenceStage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = MLInferenceService()
        cls.stage = MLInferenceStage(service=cls.service, operational_threshold=0.40)

    def test_01_stage_attributes(self):
        """Test canonical stage name and dependencies."""
        self.assertEqual(self.stage.name, "ml_inference")
        self.assertIn("forgery", self.stage.dependencies)

    def test_02_stage_run_with_populated_context(self):
        """Test that stage processes populated context and attaches ml_prediction."""
        ctx = AnalysisContext(original_filename="test_doc.tif", file_type="tif")
        
        # Simulate populated quality and forensics metrics
        from app.services.preprocessing.models import QualityMetrics
        ctx.quality_metrics = [
            QualityMetrics(width=1080, height=1920, aspect_ratio=0.5625, color_channels=3)
        ]
        ctx.image_forensics_metrics = [{
            "laplacian_variance": 130.0,
            "blur_severity": 20.0,
            "noise_sigma": 4.1,
            "edge_density": 0.026,
            "illumination_std": 51.0,
            "ela_region_count": 2.0,
            "ela_max_difference": 36.5,
            "entropy_score": 7.2,
        }]
        ctx.copy_move_features = {
            "keypoint_count_akaze": 3100.0,
            "descriptor_matches": 105.0,
            "inlier_matches": 22.0,
            "average_region_size": 1500.0,
            "duplicate_pair_count": 1.0,
            "confidence": 0.65,
            "inlier_ratio": 0.2095,
        }

        result = asyncio.run(self.stage.run(ctx))
        self.assertTrue(result.succeeded)
        self.assertIsNotNone(ctx.ml_prediction)
        self.assertIn("forgery_probability", ctx.ml_prediction)
        self.assertIn("risk_tier", ctx.ml_prediction)
        self.assertEqual(ctx.ml_prediction["operational_threshold"], 0.40)
        self.assertEqual(ctx.ml_prediction["status"], InferenceStatus.SUCCESS.value)

    def test_03_stage_run_with_empty_context(self):
        """Test that stage handles unpopulated context gracefully with warnings without raising."""
        ctx = AnalysisContext(original_filename="empty_doc.tif", file_type="tif")
        result = asyncio.run(self.stage.run(ctx))
        
        self.assertTrue(result.succeeded)
        self.assertIsNotNone(ctx.ml_prediction)
        # Should be ML_UNAVAILABLE since critical features are missing
        self.assertEqual(ctx.ml_prediction["status"], InferenceStatus.ML_UNAVAILABLE.value)
        self.assertTrue(len(ctx.ml_prediction["warnings"]) > 0)

if __name__ == "__main__":
    unittest.main()
