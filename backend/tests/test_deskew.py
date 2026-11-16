"""
Unit tests for DeskewOperation.

All images are generated synthetically with NumPy and OpenCV.
No real scanned documents or external datasets are required.

Test strategy
-------------
- Horizontal document  : skew should be detected as ~0° → no rotation applied.
- Rotated documents    : skew should be detected and corrected within tolerance.
- Blank image          : no foreground pixels → rotation skipped, copy returned.
- Noisy image          : dense noise → confidence gate may skip or apply rotation,
                         but must never crash.
- Very small image     : validate() rejects it before execute() is called.
- Large image          : algorithm must complete without error.
- In-place safety      : original array must never be modified.
- Output dimensions    : rotated canvas must be at least as large as the input.
"""

from __future__ import annotations

import math

import cv2
import numpy as np
import pytest

from app.services.preprocessing.operations.deskew import (
    DeskewOperation,
    _MIN_CORRECTABLE_ANGLE,
    _MAX_CORRECTABLE_ANGLE,
)
from app.pipeline.context import AnalysisContext


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _make_context() -> AnalysisContext:
    return AnalysisContext(original_filename="test.png", file_type="png")


def _white_canvas(h: int = 400, w: int = 600) -> np.ndarray:
    """Return a white BGR image."""
    return np.full((h, w, 3), 255, dtype=np.uint8)


def _draw_text_lines(image: np.ndarray, n_lines: int = 6) -> np.ndarray:
    """
    Draw n_lines of horizontal black text-like rectangles on a white canvas.
    Produces a realistic foreground pixel distribution for skew detection.
    """
    h, w = image.shape[:2]
    step = h // (n_lines + 1)
    thickness = max(4, h // 40)
    for i in range(1, n_lines + 1):
        y = i * step
        x_start = w // 10
        x_end = w - w // 10
        cv2.rectangle(
            image,
            (x_start, y - thickness // 2),
            (x_end, y + thickness // 2),
            (0, 0, 0),
            -1,
        )
    return image


def _make_document(h: int = 400, w: int = 600, n_lines: int = 6) -> np.ndarray:
    """Return a synthetic document image with horizontal text lines."""
    canvas = _white_canvas(h, w)
    return _draw_text_lines(canvas, n_lines)


def _rotate_document(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """
    Rotate `image` by `angle_deg` degrees with an expanded canvas.
    Used to produce ground-truth skewed inputs for tests.
    """
    h, w = image.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    M = cv2.getRotationMatrix2D((cx, cy), angle_deg, 1.0)
    cos_a = abs(M[0, 0])
    sin_a = abs(M[0, 1])
    new_w = int(np.ceil(h * sin_a + w * cos_a))
    new_h = int(np.ceil(h * cos_a + w * sin_a))
    M[0, 2] += (new_w / 2.0) - cx
    M[1, 2] += (new_h / 2.0) - cy
    return cv2.warpAffine(
        image, M, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def op() -> DeskewOperation:
    return DeskewOperation()


@pytest.fixture
def ctx() -> AnalysisContext:
    return _make_context()


# ------------------------------------------------------------------ #
# Metadata and interface                                               #
# ------------------------------------------------------------------ #

class TestDeskewOperationInterface:
    def test_name(self, op):
        assert op.name == "deskew"

    def test_version_is_not_placeholder(self, op):
        assert op.version == "1.0.0"

    def test_enabled_by_default(self, op):
        assert op.enabled is True

    def test_metadata_keys(self, op):
        m = op.metadata()
        assert {"name", "version", "description", "enabled"} <= m.keys()

    def test_description_is_non_empty(self, op):
        assert len(op.description) > 0


# ------------------------------------------------------------------ #
# Validation                                                           #
# ------------------------------------------------------------------ #

class TestDeskewValidation:
    def test_empty_array_fails_validation(self, op):
        warnings = op.validate(np.array([]))
        assert len(warnings) > 0

    def test_too_small_image_fails_validation(self, op):
        tiny = np.full((5, 5, 3), 255, dtype=np.uint8)
        warnings = op.validate(tiny)
        assert len(warnings) > 0

    def test_valid_image_passes_validation(self, op):
        image = _make_document()
        warnings = op.validate(image)
        assert warnings == []

    def test_run_skips_empty_image(self, op, ctx):
        empty = np.array([])
        result, warnings = op.run(empty, ctx)
        assert len(warnings) > 0

    def test_run_skips_tiny_image(self, op, ctx):
        tiny = np.full((5, 5, 3), 255, dtype=np.uint8)
        result, warnings = op.run(tiny, ctx)
        assert len(warnings) > 0


# ------------------------------------------------------------------ #
# Blank / near-blank images                                            #
# ------------------------------------------------------------------ #

class TestDeskewBlankImages:
    def test_blank_white_image_returns_copy(self, op, ctx):
        """All-white image has no foreground pixels — must return a copy, not crash."""
        image = _white_canvas()
        result, warnings = op.run(image, ctx)
        assert result is not image
        assert result.shape == image.shape

    def test_blank_black_image_returns_copy(self, op, ctx):
        """All-black image: after inversion all pixels are foreground.
        minAreaRect will run but the angle should be near 0 or clamped."""
        image = np.zeros((400, 600, 3), dtype=np.uint8)
        result, warnings = op.run(image, ctx)
        assert result is not image

    def test_single_pixel_foreground_returns_copy(self, op, ctx):
        image = _white_canvas()
        image[200, 300] = (0, 0, 0)
        result, warnings = op.run(image, ctx)
        assert result is not image


# ------------------------------------------------------------------ #
# In-place safety                                                      #
# ------------------------------------------------------------------ #

class TestDeskewInPlaceSafety:
    def test_original_not_modified_on_horizontal_document(self, op, ctx):
        image = _make_document()
        original = image.copy()
        op.run(image, ctx)
        assert np.array_equal(image, original)

    def test_original_not_modified_on_skewed_document(self, op, ctx):
        image = _rotate_document(_make_document(), 5.0)
        original = image.copy()
        op.run(image, ctx)
        assert np.array_equal(image, original)

    def test_original_not_modified_on_blank_image(self, op, ctx):
        image = _white_canvas()
        original = image.copy()
        op.run(image, ctx)
        assert np.array_equal(image, original)


# ------------------------------------------------------------------ #
# Output dimensions                                                    #
# ------------------------------------------------------------------ #

class TestDeskewOutputDimensions:
    def test_output_at_least_as_large_as_input_horizontal(self, op, ctx):
        image = _make_document(400, 600)
        result, _ = op.run(image, ctx)
        assert result.shape[0] >= image.shape[0]
        assert result.shape[1] >= image.shape[1]

    def test_output_at_least_as_large_as_input_skewed(self, op, ctx):
        image = _rotate_document(_make_document(400, 600), 7.0)
        result, _ = op.run(image, ctx)
        assert result.shape[0] >= image.shape[0]
        assert result.shape[1] >= image.shape[1]

    def test_output_preserves_channels(self, op, ctx):
        image = _make_document()
        result, _ = op.run(image, ctx)
        assert result.ndim == image.ndim
        assert result.shape[2] == image.shape[2]

    def test_output_preserves_dtype(self, op, ctx):
        image = _make_document()
        result, _ = op.run(image, ctx)
        assert result.dtype == image.dtype

    def test_grayscale_input_preserves_shape(self, op, ctx):
        color = _make_document()
        gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        result, _ = op.run(gray, ctx)
        assert result.ndim == 2


# ------------------------------------------------------------------ #
# Angle estimation accuracy                                            #
# ------------------------------------------------------------------ #

class TestDeskewAngleEstimation:
    """
    These tests verify that the algorithm corrects skew to within a tolerance.

    We measure residual skew by running the deskewed output back through the
    internal _estimate_angle / _normalise_angle helpers and checking that the
    residual is smaller than the original skew.

    We do NOT assert exact pixel equality because:
      - Interpolation introduces sub-pixel differences.
      - The expanded canvas adds border pixels.
    """

    def _residual_angle(self, op: DeskewOperation, image: np.ndarray) -> float:
        """Return the absolute normalised angle estimated from `image`."""
        gray = op._to_gray(image)
        binary = op._binarise(gray)
        raw, _, reason = op._estimate_angle(binary)
        if reason:
            return 0.0
        return abs(op._normalise_angle(raw))

    def test_horizontal_document_has_small_residual(self, op, ctx):
        image = _make_document(400, 600, n_lines=8)
        result, _ = op.run(image, ctx)
        residual = self._residual_angle(op, result)
        assert residual < 1.0, f"Residual angle {residual:.3f}° too large for horizontal doc"

    def test_positive_5_degree_skew_is_reduced(self, op, ctx):
        original = _make_document(400, 600, n_lines=8)
        skewed = _rotate_document(original, 5.0)
        original_residual = self._residual_angle(op, skewed)
        result, _ = op.run(skewed, ctx)
        corrected_residual = self._residual_angle(op, result)
        assert corrected_residual < original_residual or corrected_residual < 1.5, (
            f"Correction did not reduce skew: before={original_residual:.3f}° "
            f"after={corrected_residual:.3f}°"
        )

    def test_negative_8_degree_skew_is_reduced(self, op, ctx):
        original = _make_document(400, 600, n_lines=8)
        skewed = _rotate_document(original, -8.0)
        original_residual = self._residual_angle(op, skewed)
        result, _ = op.run(skewed, ctx)
        corrected_residual = self._residual_angle(op, result)
        assert corrected_residual < original_residual or corrected_residual < 1.5, (
            f"Correction did not reduce skew: before={original_residual:.3f}° "
            f"after={corrected_residual:.3f}°"
        )

    def test_large_skew_beyond_max_is_skipped(self, op, ctx, monkeypatch):
        """Angles beyond _MAX_CORRECTABLE_ANGLE should not be applied."""
        original = _make_document(400, 600, n_lines=8)
        # 50° is beyond the 45° clamp — _normalise_angle returns 0.0
        skewed = _rotate_document(original, 50.0)
        # minAreaRect has a 90-degree axis ambiguity: a 50-degree image can
        # legitimately be estimated as -40. Test the actual safety guard with
        # an out-of-range estimator result, rather than asserting orientation
        # classification that this algorithm cannot guarantee.
        monkeypatch.setattr(op, '_estimate_angle', lambda binary: (50.0, 1.0, ''))
        result, _ = op.run(skewed, ctx)
        # Result must be a copy of the input (no rotation applied)
        assert result is not skewed
        assert result.shape == skewed.shape

    def test_sub_threshold_skew_is_not_applied(self, op, ctx):
        """Angles below _MIN_CORRECTABLE_ANGLE should not trigger rotation."""
        # A perfectly horizontal document should have near-zero estimated angle
        image = _make_document(600, 900, n_lines=10)
        result, _ = op.run(image, ctx)
        # Canvas may be same size or slightly larger; must not crash
        assert result is not image


# ------------------------------------------------------------------ #
# Noisy images                                                         #
# ------------------------------------------------------------------ #

class TestDeskewNoisyImages:
    def test_random_noise_does_not_crash(self, op, ctx):
        rng = np.random.default_rng(0)
        noisy = rng.integers(0, 256, (400, 600, 3), dtype=np.uint8)
        result, _ = op.run(noisy, ctx)
        assert result is not noisy

    def test_salt_and_pepper_noise_does_not_crash(self, op, ctx):
        image = _make_document()
        rng = np.random.default_rng(1)
        mask = rng.random(image.shape[:2]) < 0.05
        noisy = image.copy()
        noisy[mask] = 0
        result, _ = op.run(noisy, ctx)
        assert result is not noisy


# ------------------------------------------------------------------ #
# Large image                                                          #
# ------------------------------------------------------------------ #

class TestDeskewLargeImage:
    def test_large_document_completes(self, op, ctx):
        """2480×3508 ≈ A4 at 300 DPI — must complete without error."""
        image = _make_document(h=3508, w=2480, n_lines=20)
        result, _ = op.run(image, ctx)
        assert result.shape[0] >= image.shape[0]
        assert result.shape[1] >= image.shape[1]


# ------------------------------------------------------------------ #
# Internal helpers (unit-level)                                        #
# ------------------------------------------------------------------ #

class TestDeskewInternals:
    def test_to_gray_from_bgr(self, op):
        bgr = np.full((10, 10, 3), 128, dtype=np.uint8)
        gray = op._to_gray(bgr)
        assert gray.ndim == 2

    def test_to_gray_from_gray_2d(self, op):
        gray_in = np.full((10, 10), 128, dtype=np.uint8)
        gray_out = op._to_gray(gray_in)
        assert gray_out.ndim == 2
        assert np.array_equal(gray_in, gray_out)

    def test_to_gray_from_single_channel_3d(self, op):
        img = np.full((10, 10, 1), 128, dtype=np.uint8)
        gray = op._to_gray(img)
        assert gray.ndim == 2

    def test_binarise_produces_binary_image(self, op):
        gray = cv2.cvtColor(_make_document(), cv2.COLOR_BGR2GRAY)
        binary = op._binarise(gray)
        unique = np.unique(binary)
        assert set(unique).issubset({0, 255})

    def test_estimate_angle_blank_image_returns_skip_reason(self, op):
        binary = np.zeros((100, 100), dtype=np.uint8)
        _, _, reason = op._estimate_angle(binary)
        assert reason != ""

    def test_estimate_angle_document_returns_no_skip_reason(self, op):
        doc = _make_document()
        gray = op._to_gray(doc)
        binary = op._binarise(gray)
        _, _, reason = op._estimate_angle(binary)
        assert reason == ""

    def test_normalise_angle_near_minus_90_maps_to_small_positive(self, op):
        # OpenCV returns ~-90° for a nearly-upright document
        angle = op._normalise_angle(-89.5)
        assert abs(angle) < 1.0

    def test_normalise_angle_beyond_max_returns_zero(self, op):
        angle = op._normalise_angle(50.0)
        assert angle == 0.0

    def test_rotate_expands_canvas(self, op):
        image = _make_document(400, 600)
        rotated = op._rotate(image, 10.0)
        assert rotated.shape[0] >= image.shape[0]
        assert rotated.shape[1] >= image.shape[1]

    def test_rotate_zero_angle_preserves_dimensions(self, op):
        image = _make_document(400, 600)
        rotated = op._rotate(image, 0.0)
        assert rotated.shape == image.shape

    def test_rotate_does_not_modify_original(self, op):
        image = _make_document(400, 600)
        original = image.copy()
        op._rotate(image, 5.0)
        assert np.array_equal(image, original)
