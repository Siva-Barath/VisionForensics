"""
Unit tests for the preprocessing subsystem.

All tests use synthetic NumPy images — no real files or external datasets required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.preprocessing.models import QualityMetrics, PreprocessingSummary
from app.services.preprocessing.quality_analyzer import QualityAnalyzer
from app.services.preprocessing.decision_engine import DecisionEngine
from app.services.preprocessing.operations import (
    OperationRegistry,
    build_default_registry,
    DeskewOperation,
    ContrastEnhancementOperation,
    DenoiseOperation,
    NormalizationOperation,
    ShadowRemovalOperation,
    PerspectiveCorrectionOperation,
)
from app.pipeline.context import AnalysisContext


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _gray_image(brightness: int = 128, size: tuple = (100, 100)) -> np.ndarray:
    """Return a uniform grayscale image."""
    return np.full((*size, 1), brightness, dtype=np.uint8)


def _bgr_image(brightness: int = 128, size: tuple = (100, 100)) -> np.ndarray:
    """Return a uniform BGR image."""
    return np.full((*size, 3), brightness, dtype=np.uint8)


def _noisy_image(size: tuple = (100, 100)) -> np.ndarray:
    """Return a BGR image with random noise (high blur score)."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (*size, 3), dtype=np.uint8)


def _make_context() -> AnalysisContext:
    return AnalysisContext(original_filename="test.png", file_type="png")


# ------------------------------------------------------------------ #
# QualityAnalyzer                                                      #
# ------------------------------------------------------------------ #

class TestQualityAnalyzer:
    def setup_method(self):
        self.analyzer = QualityAnalyzer()

    def test_returns_quality_metrics_instance(self):
        image = _bgr_image()
        result = self.analyzer.analyze(image)
        assert isinstance(result, QualityMetrics)

    def test_dimensions_are_correct(self):
        image = _bgr_image(size=(80, 120))
        metrics = self.analyzer.analyze(image)
        assert metrics.height == 80
        assert metrics.width == 120

    def test_aspect_ratio(self):
        image = _bgr_image(size=(100, 200))
        metrics = self.analyzer.analyze(image)
        assert abs(metrics.aspect_ratio - 2.0) < 0.01

    def test_color_channels_bgr(self):
        image = _bgr_image()
        metrics = self.analyzer.analyze(image)
        assert metrics.color_channels == 3

    def test_brightness_uniform_image(self):
        image = _bgr_image(brightness=100)
        metrics = self.analyzer.analyze(image)
        assert abs(metrics.brightness - 100.0) < 1.0

    def test_contrast_uniform_image_is_zero(self):
        image = _bgr_image(brightness=128)
        metrics = self.analyzer.analyze(image)
        assert metrics.contrast < 1.0

    def test_blur_score_noisy_image_is_high(self):
        image = _noisy_image()
        metrics = self.analyzer.analyze(image)
        assert metrics.blur_score > 0

    def test_orientation_is_none_placeholder(self):
        metrics = self.analyzer.analyze(_bgr_image())
        assert metrics.orientation is None

    def test_skew_angle_is_none_placeholder(self):
        metrics = self.analyzer.analyze(_bgr_image())
        assert metrics.skew_angle is None

    def test_empty_image_returns_warning(self):
        empty = np.array([])
        metrics = self.analyzer.analyze(empty)
        assert len(metrics.warnings) > 0

    def test_size_bytes_stored(self):
        image = _bgr_image()
        metrics = self.analyzer.analyze(image, size_bytes=12345)
        assert metrics.size_bytes == 12345


# ------------------------------------------------------------------ #
# OperationRegistry                                                    #
# ------------------------------------------------------------------ #

class TestOperationRegistry:
    def test_register_and_get(self):
        registry = OperationRegistry()
        op = DeskewOperation()
        registry.register(op)
        assert registry.get("deskew") is op

    def test_get_unknown_returns_none(self):
        registry = OperationRegistry()
        assert registry.get("nonexistent") is None

    def test_names_returns_all_registered(self):
        registry = build_default_registry()
        names = registry.names()
        assert "deskew" in names
        assert "contrast" in names
        assert "denoise" in names
        assert "normalize" in names
        assert "shadow" in names
        assert "perspective" in names

    def test_len(self):
        registry = build_default_registry()
        assert len(registry) == 6

    def test_replace_existing(self):
        registry = OperationRegistry()
        op1 = DeskewOperation()
        op2 = DeskewOperation()
        registry.register(op1)
        registry.register(op2)
        assert registry.get("deskew") is op2

    def test_get_all_returns_list(self):
        registry = build_default_registry()
        ops = registry.get_all()
        assert isinstance(ops, list)
        assert len(ops) == 6


# ------------------------------------------------------------------ #
# DecisionEngine                                                       #
# ------------------------------------------------------------------ #

class TestDecisionEngine:
    def setup_method(self):
        self.registry = build_default_registry()
        self.engine = DecisionEngine(self.registry)

    def _metrics(self, **overrides) -> QualityMetrics:
        defaults = dict(
            width=800, height=600, aspect_ratio=1.33,
            color_channels=3, size_bytes=50000,
            brightness=128.0, contrast=60.0, blur_score=200.0,
            orientation=None, skew_angle=None,
        )
        defaults.update(overrides)
        return QualityMetrics(**defaults)

    def test_no_operations_for_good_image(self):
        metrics = self._metrics()
        ops = self.engine.select(metrics)
        # Good image: blur_score=200 (above threshold), contrast=60 (above threshold)
        # normalize is only added when other ops are selected
        assert all(op.name != "denoise" for op in ops)
        assert all(op.name != "contrast" for op in ops)

    def test_denoise_selected_for_blurry_image(self):
        metrics = self._metrics(blur_score=50.0)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "denoise" in names

    def test_contrast_selected_for_low_contrast(self):
        metrics = self._metrics(contrast=20.0)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "contrast" in names

    def test_contrast_selected_for_dark_image(self):
        metrics = self._metrics(brightness=30.0)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "contrast" in names

    def test_normalize_selected_for_bright_image(self):
        metrics = self._metrics(brightness=220.0)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "normalize" in names

    def test_deskew_not_selected_when_skew_is_none(self):
        metrics = self._metrics(skew_angle=None)
        ops = self.engine.select(metrics)
        assert all(op.name != "deskew" for op in ops)

    def test_deskew_selected_when_skew_exceeds_threshold(self):
        metrics = self._metrics(skew_angle=2.5)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "deskew" in names

    def test_normalize_appended_when_other_ops_selected(self):
        # Low blur triggers denoise; normalize should be appended
        metrics = self._metrics(blur_score=50.0)
        ops = self.engine.select(metrics)
        names = [op.name for op in ops]
        assert "normalize" in names
        assert names[-1] == "normalize"

    def test_disabled_operation_not_returned(self):
        registry = build_default_registry()
        registry.get("denoise").enabled = False
        engine = DecisionEngine(registry)
        metrics = self._metrics(blur_score=50.0)
        ops = engine.select(metrics)
        assert all(op.name != "denoise" for op in ops)


# ------------------------------------------------------------------ #
# Placeholder operations — all must return image unchanged            #
# ------------------------------------------------------------------ #

class TestPlaceholderOperations:
    def setup_method(self):
        self.context = _make_context()
        self.image = _bgr_image()

    def _run(self, op):
        result, warnings = op.run(self.image, self.context)
        return result, warnings

    def test_deskew_does_not_crash_on_uniform_image(self):
        # A uniform image has no foreground pixels — deskew should return a copy
        result, warnings = self._run(DeskewOperation())
        assert result is not self.image
        assert result.shape == self.image.shape

    def test_disabled_op_returns_original_with_warning(self):
        op = DeskewOperation()
        op.enabled = False
        result, warnings = op.run(self.image, self.context)
        assert np.array_equal(result, self.image)
        assert len(warnings) == 1

    def test_empty_image_triggers_validation_warning(self):
        op = DeskewOperation()
        empty = np.array([])
        result, warnings = op.run(empty, self.context)
        assert len(warnings) > 0

# ------------------------------------------------------------------ #
# PerspectiveCorrectionOperation                                       #
# ------------------------------------------------------------------ #

class TestPerspectiveCorrectionOperation:
    def setup_method(self):
        self.context = _make_context()
        self.op = PerspectiveCorrectionOperation()

    def _run(self, image):
        result, warnings = self.op.run(image, self.context)
        return result, warnings

    def _draw_rect(self, img, pts, color=255):
        import cv2
        cv2.fillPoly(img, [pts.astype(int)], color)

    def test_perfectly_aligned_document(self):
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        pts = np.array([[100, 100], [400, 100], [400, 400], [100, 400]], dtype=np.int32)
        self._draw_rect(img, pts, color=(255, 255, 255))
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["perspective_applied"] is True
        assert result.shape[0] == 300
        assert result.shape[1] == 300
        assert img[0, 0, 0] == 0  # ensure input is unchanged

    def test_perspective_distorted_document(self):
        img = np.zeros((500, 500), dtype=np.uint8)
        pts = np.array([[150, 100], [450, 150], [400, 450], [100, 400]], dtype=np.int32)
        self._draw_rect(img, pts)
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["perspective_applied"] is True
        assert "transform_matrix" in self.context.metadata

    def test_blank_image(self):
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert self.context.metadata["document_found"] is False
        assert self.context.metadata["perspective_applied"] is False
        assert np.array_equal(result, img)
        assert result is not img

    def test_noisy_image(self):
        img = _noisy_image((500, 500))
        result, warnings = self._run(img)
        assert self.context.metadata["perspective_applied"] is False
        assert np.array_equal(result, img)

    def test_partially_visible_document(self):
        img = np.zeros((500, 500), dtype=np.uint8)
        pts = np.array([[100, 100], [400, 100], [400, 400]], dtype=np.int32) # Triangle
        self._draw_rect(img, pts)
        
        result, warnings = self._run(img)
        assert self.context.metadata["perspective_applied"] is False
        assert np.array_equal(result, img)

    def test_very_small_image(self):
        img = np.zeros((50, 50), dtype=np.uint8)
        pts = np.array([[10, 10], [40, 10], [40, 40], [10, 40]], dtype=np.int32)
        self._draw_rect(img, pts)
        
        result, warnings = self._run(img)
        assert self.context.metadata["perspective_applied"] is True

    def test_large_scanned_document(self):
        img = np.zeros((2000, 1500), dtype=np.uint8)
        pts = np.array([[200, 200], [1300, 250], [1400, 1800], [100, 1700]], dtype=np.int32)
        self._draw_rect(img, pts)
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["perspective_applied"] is True


# ------------------------------------------------------------------ #
# DenoiseOperation                                                     #
# ------------------------------------------------------------------ #

class TestDenoiseOperation:
    def setup_method(self):
        self.context = _make_context()
        self.op = DenoiseOperation()

    def _run(self, image):
        result, warnings = self.op.run(image, self.context)
        return result, warnings

    def test_clean_document(self):
        img = _bgr_image()
        # Add a simple text-like structure
        img[20:30, 20:80] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is False
        assert self.context.metadata["algorithm_used"] == "skip"
        assert result is not img
        assert np.array_equal(result, img)

    def test_gaussian_noise(self):
        img = _bgr_image()
        # Add moderate noise
        noise = np.random.normal(0, 10, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        result, warnings = self._run(noisy)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is True
        assert self.context.metadata["algorithm_used"] in ["fast_nl_means", "bilateral_filter", "median_blur"]
        assert result.shape == noisy.shape

    def test_salt_and_pepper_noise(self):
        img = _bgr_image()
        # Add salt and pepper noise
        mask_salt = np.random.rand(*img.shape[:2]) > 0.95
        mask_pepper = np.random.rand(*img.shape[:2]) < 0.05
        
        img[mask_salt] = 255
        img[mask_pepper] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is True
        assert self.context.metadata["algorithm_used"] == "median_blur"
        assert result.shape == img.shape

    def test_jpeg_like_noisy_image(self):
        img = _bgr_image()
        # Add very slight noise simulating JPEG
        noise = np.random.normal(0, 3, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        result, warnings = self._run(noisy)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is True
        assert self.context.metadata["algorithm_used"] in ["bilateral_filter", "fast_nl_means", "median_blur", "skip"]
        assert result.shape == noisy.shape

    def test_blank_image(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is False
        assert self.context.metadata["algorithm_used"] == "skip"
        assert np.array_equal(result, img)
        assert result is not img

    def test_very_small_image(self):
        img = _bgr_image(size=(5, 5))
        result, warnings = self._run(img)
        assert len(warnings) > 0 or result.shape == img.shape
        assert result.shape == img.shape

    def test_high_resolution_scanned_document(self):
        img = _bgr_image(size=(200, 150)) # Using smaller sizes to avoid very slow test
        img[50:55, 50:100] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["denoise_applied"] is False
        assert self.context.metadata["algorithm_used"] == "skip"
        assert result.shape == img.shape


# ------------------------------------------------------------------ #
# ContrastEnhancementOperation                                         #
# ------------------------------------------------------------------ #

class TestContrastEnhancementOperation:
    def setup_method(self):
        self.context = _make_context()
        self.op = ContrastEnhancementOperation()

    def _run(self, image):
        result, warnings = self.op.run(image, self.context)
        return result, warnings

    def test_high_contrast_document_skips(self):
        img = _bgr_image(brightness=255)
        img[20:80, 20:80] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is False
        assert self.context.metadata["algorithm_used"] == "skip"
        assert result is not img
        assert np.array_equal(result, img)

    def test_low_contrast_document_applies_clahe(self):
        img = _bgr_image(brightness=128)
        img[20:80, 20:80] = 135
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert self.context.metadata["algorithm_used"] == "clahe_lab"
        assert self.context.metadata["contrast_after"] > self.context.metadata["contrast_before"]
        assert result.shape == img.shape

    def test_dark_scanned_page(self):
        img = _bgr_image(brightness=20)
        img[20:80, 20:80] = 30
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert self.context.metadata["brightness_after"] > self.context.metadata["brightness_before"]

    def test_grayscale_document(self):
        img = _gray_image(brightness=128)
        img[20:80, 20:80] = 135
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert self.context.metadata["algorithm_used"] == "clahe_gray"
        assert result.shape == img.shape

    def test_color_document(self):
        img = np.full((100, 100, 3), (100, 150, 200), dtype=np.uint8)
        img[20:80, 20:80] = (110, 160, 210)
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert self.context.metadata["algorithm_used"] == "clahe_lab"

    def test_blank_image(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert result.shape == img.shape

    def test_small_image(self):
        img = _bgr_image(brightness=128, size=(10, 10))
        img[2:8, 2:8] = 135
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True

    def test_high_resolution_document(self):
        img = _bgr_image(brightness=128, size=(2000, 1500))
        img[500:600, 500:600] = 135
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["contrast_enhancement_applied"] is True
        assert result.shape == img.shape


# ------------------------------------------------------------------ #
# ShadowRemovalOperation                                               #
# ------------------------------------------------------------------ #

class TestShadowRemovalOperation:
    def setup_method(self):
        self.context = _make_context()
        self.op = ShadowRemovalOperation()

    def _run(self, image):
        result, warnings = self.op.run(image, self.context)
        return result, warnings

    def _create_gradient_image(self, size, start_val, end_val):
        import cv2
        img = np.zeros(size, dtype=np.float32)
        for i in range(size[1]):
            img[:, i] = start_val + (end_val - start_val) * (i / size[1])
        return img.astype(np.uint8)

    def test_clean_document_skips(self):
        img = np.full((100, 100, 3), 200, dtype=np.uint8)
        # Thin printed strokes are foreground; a 60x60 dark block is genuine
        # large-scale illumination variation, not a uniformly lit control.
        img[20:80:8, 20:80] = 50
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is False
        assert self.context.metadata["algorithm_used"] == "skip"
        assert result is not img
        assert np.array_equal(result, img)

    def test_document_with_shadow_gradient(self):
        import cv2
        gray = self._create_gradient_image((100, 100), 50, 250)
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        img[40:60, 40:60] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is True
        
        bg_after = self.context.metadata["illumination_variance_after"]
        bg_before = self.context.metadata["illumination_variance_before"]
        assert bg_after < bg_before
        assert result.shape == img.shape

    def test_uneven_illumination(self):
        import cv2
        img = np.full((100, 100), 200, dtype=np.uint8)
        cv2.circle(img, (50, 50), 30, 80, -1)
        img[20:30, 20:80] = 0
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is True
        assert self.context.metadata["illumination_variance_after"] < self.context.metadata["illumination_variance_before"]

    def test_color_document(self):
        gray = self._create_gradient_image((100, 100), 50, 250)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 0] = gray
        img[:, :, 1] = gray
        img[:, :, 2] = 200
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is True
        assert result.shape == img.shape

    def test_grayscale_document(self):
        gray = self._create_gradient_image((100, 100), 100, 255)
        
        result, warnings = self._run(gray)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is True
        assert result.shape == gray.shape

    def test_blank_image(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is False
        assert result.shape == img.shape

    def test_small_image(self):
        img = self._create_gradient_image((10, 10), 50, 250)
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        # Below the background kernel size, the illumination estimate is
        # uniform; no correction should be claimed or pixels changed.
        assert self.context.metadata["shadow_removal_applied"] is False
        assert np.array_equal(result, img)

    def test_high_resolution_scan(self):
        img = self._create_gradient_image((1500, 2000), 100, 250)
        
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["shadow_removal_applied"] is True
        assert result.shape == img.shape


# ------------------------------------------------------------------ #
# NormalizationOperation                                               #
# ------------------------------------------------------------------ #

class TestNormalizationOperation:
    def setup_method(self):
        self.context = _make_context()
        self.op = NormalizationOperation()

    def _run(self, image):
        result, warnings = self.op.run(image, self.context)
        return result, warnings

    def test_already_normalized_skips(self):
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is False
        assert result is not img
        assert np.array_equal(result, img)

    def test_very_small_image_upscales(self):
        img = np.zeros((400, 300, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is True
        assert self.context.metadata["resize_scale"] > 1.0
        assert min(result.shape[:2]) == self.op.MIN_DIMENSION

    def test_very_large_image_downscales(self):
        img = np.zeros((5000, 2000, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is True
        assert self.context.metadata["resize_scale"] < 1.0
        assert max(result.shape[:2]) == self.op.MAX_DIMENSION

    def test_grayscale_image_preserved(self):
        img = np.zeros((1000, 1000), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is False
        assert len(result.shape) == 2

    def test_color_image_preserves_bgr(self):
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is False
        assert result.shape[2] == 3

    def test_bgra_strips_alpha(self):
        import cv2
        img = np.zeros((1000, 1000, 4), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is True
        assert result.shape[2] == 3

    def test_invalid_values_fails_gracefully(self):
        img = np.zeros((1000, 1000, 3), dtype=np.float32)
        img[0, 0, 0] = np.nan
        result, warnings = self._run(img)
        assert len(warnings) > 0
        assert self.context.metadata["normalization_applied"] is False
        assert np.array_equal(result, img, equal_nan=True)

    def test_float_to_uint8(self):
        img = np.full((1000, 1000, 3), 0.5, dtype=np.float32)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is True
        assert result.dtype == np.uint8
        assert np.mean(result) > 100

    def test_blank_image(self):
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        result, warnings = self._run(img)
        assert len(warnings) == 0
        assert self.context.metadata["normalization_applied"] is False
        assert result.shape == img.shape


# ------------------------------------------------------------------ #
# PreprocessingService                                                 #
# ------------------------------------------------------------------ #

class TestPreprocessingService:
    """
    Tests PreprocessingService using a temporary directory and real PNG files
    written with cv2 so no mocking of file I/O is needed.
    """

    def setup_method(self, tmp_path_factory=None):
        import tempfile
        self._tmpdir = Path(tempfile.mkdtemp())

    def _write_png(self, name: str, image: np.ndarray) -> str:
        import cv2
        path = self._tmpdir / name
        cv2.imwrite(str(path), image)
        return str(path)

    def _make_service(self):
        from app.services.preprocessing.preprocessor import PreprocessingService
        return PreprocessingService(output_dir=self._tmpdir)

    def test_process_returns_stage_result(self):
        from app.pipeline.stage_result import StageResult
        image = _bgr_image()
        path = self._write_png("page_0.png", image)
        context = _make_context()
        context.page_images = [path]

        service = self._make_service()
        result = service.process(context)

        assert isinstance(result, StageResult)
        assert result.status == "success"

    def test_process_populates_preprocessed_images(self):
        image = _bgr_image()
        path = self._write_png("page_0.png", image)
        context = _make_context()
        context.page_images = [path]

        service = self._make_service()
        service.process(context)

        assert len(context.preprocessed_images) == 1

    def test_process_populates_quality_metrics(self):
        image = _bgr_image()
        path = self._write_png("page_0.png", image)
        context = _make_context()
        context.page_images = [path]

        service = self._make_service()
        service.process(context)

        assert len(context.quality_metrics) == 1
        assert isinstance(context.quality_metrics[0], QualityMetrics)

    def test_process_populates_preprocessing_summary(self):
        image = _bgr_image()
        path = self._write_png("page_0.png", image)
        context = _make_context()
        context.page_images = [path]

        service = self._make_service()
        service.process(context)

        assert len(context.preprocessing_summary) == 1
        assert isinstance(context.preprocessing_summary[0], PreprocessingSummary)

    def test_process_registers_artifacts(self):
        image = _bgr_image()
        path = self._write_png("page_0.png", image)
        context = _make_context()
        context.page_images = [path]

        service = self._make_service()
        service.process(context)

        artifacts = context.get_artifact_by_type("preprocessed_image")
        assert len(artifacts) == 1
        assert Path(artifacts[0].path).exists()

    def test_process_multiple_pages(self):
        context = _make_context()
        context.page_images = [
            self._write_png(f"page_{i}.png", _bgr_image(brightness=50 + i * 30))
            for i in range(3)
        ]

        service = self._make_service()
        result = service.process(context)

        assert result.metadata["pages_processed"] == 3
        assert len(context.quality_metrics) == 3
        assert len(context.preprocessing_summary) == 3

    def test_process_empty_page_images_returns_warning(self):
        context = _make_context()
        context.page_images = []

        service = self._make_service()
        result = service.process(context)

        assert result.status == "success"
        assert len(result.warnings) > 0

    def test_process_missing_file_adds_warning(self):
        context = _make_context()
        context.page_images = [str(self._tmpdir / "nonexistent.png")]

        service = self._make_service()
        result = service.process(context)

        assert result.status == "success"
        assert any("Could not load" in w for w in result.warnings)
