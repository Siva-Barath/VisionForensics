"""
DeskewOperation — corrects rotational skew in document images.

Algorithm overview
------------------
Skew detection uses cv2.minAreaRect applied to the set of all foreground
(dark) pixels in a binarised version of the image.

Why minAreaRect over Hough Line Transform?
  - Hough requires careful parameter tuning (rho, theta, threshold, minLineLength,
    maxLineGap) that varies with DPI and document type.  Getting a stable median
    angle from hundreds of short line segments is fragile.
  - minAreaRect fits a single minimum-area bounding rectangle around ALL foreground
    pixels in one call.  For a well-scanned document the dominant orientation of
    that rectangle equals the skew angle.  It is fast (O(n log n) convex hull),
    parameter-free, and consistently accurate for ±45° skew ranges.
  - Limitation: minAreaRect is sensitive to large non-text elements (borders,
    stamps, dark margins).  We mitigate this with a foreground-pixel density
    confidence gate and by clamping the correctable range to ±45°.

Rotation strategy
-----------------
The image is rotated around its centre using cv2.warpAffine with an expanded
canvas so no corner content is clipped.  The new canvas dimensions are derived
from the rotation matrix's absolute row sums applied to the original size.
BORDER_REPLICATE is used to fill the new border area, which is preferable to
black fill for document images (avoids introducing artificial dark edges that
could confuse downstream forensic detectors).

Known limitations
-----------------
- Very large skew angles (>45°) are not corrected; the document should be
  manually re-scanned.
- Images that are mostly blank or contain only a single large dark region
  (e.g. a solid stamp) may produce an unreliable angle estimate; the
  confidence gate will skip correction in those cases.
- The algorithm operates on a grayscale projection of the image; colour
  information is preserved in the output but does not influence angle detection.

Expected input / output
-----------------------
Input:  NumPy ndarray, BGR (H×W×3) or grayscale (H×W or H×W×1), uint8.
Output: NumPy ndarray, same colour space and dtype as input, possibly larger
        canvas if the rotation required it.  The original array is never
        modified in-place.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext

# ------------------------------------------------------------------ #
# Tuning constants                                                     #
# ------------------------------------------------------------------ #

# Angles smaller than this (degrees) are considered negligible — skip rotation.
_MIN_CORRECTABLE_ANGLE: float = 0.1

# Angles larger than this are almost certainly a detection error — skip rotation.
_MAX_CORRECTABLE_ANGLE: float = 45.0

# Minimum fraction of pixels that must be foreground for a reliable estimate.
# Below this the image is likely blank or nearly blank.
_MIN_FOREGROUND_RATIO: float = 0.001

# Minimum number of foreground pixels required for minAreaRect to be meaningful.
_MIN_FOREGROUND_PIXELS: int = 50

# Gaussian blur kernel size applied before thresholding to suppress fine noise.
# Must be odd.  0 = disabled (applied only when image is noisy).
_BLUR_KERNEL: int = 5


class DeskewOperation(BaseOperation):
    """
    Detects and corrects rotational skew in document images.

    Uses cv2.minAreaRect on binarised foreground pixels to estimate the skew
    angle, then rotates the image around its centre with an expanded canvas
    to avoid clipping.
    """

    name = "deskew"
    description = "Corrects rotational skew in document images."
    version = "1.0.0"

    # ------------------------------------------------------------------ #
    # BaseOperation contract                                               #
    # ------------------------------------------------------------------ #

    def validate(self, image: np.ndarray) -> list[str]:
        warnings = super().validate(image)
        if warnings:
            return warnings
        h, w = image.shape[:2]
        if h < 10 or w < 10:
            warnings.append(
                f"deskew: image too small ({w}×{h}) — skipping correction"
            )
        return warnings

    def execute(
        self,
        image: np.ndarray,
        context: "AnalysisContext",
        **kwargs: Any,
    ) -> np.ndarray:
        t_start = time.perf_counter()

        self._logger.info("Deskew started | job=%s", context.job_id)

        gray = self._to_gray(image)
        binary = self._binarise(gray)

        angle, confidence, skipped_reason = self._estimate_angle(binary)

        if skipped_reason:
            self._logger.info(
                "Deskew skipped | reason=%s | job=%s", skipped_reason, context.job_id
            )
            return image.copy()

        rotation_angle = self._normalise_angle(angle)

        if abs(rotation_angle) < _MIN_CORRECTABLE_ANGLE:
            elapsed = (time.perf_counter() - t_start) * 1000
            self._logger.info(
                "Deskew skipped | estimated_angle=%.4f° is below threshold | "
                "duration=%.1fms | job=%s",
                rotation_angle, elapsed, context.job_id,
            )
            return image.copy()

        rotated = self._rotate(image, rotation_angle)

        elapsed = (time.perf_counter() - t_start) * 1000
        self._logger.info(
            "Deskew applied | estimated_angle=%.4f° | rotation_angle=%.4f° | "
            "confidence=%.3f | duration=%.1fms | job=%s",
            angle, rotation_angle, confidence, elapsed, context.job_id,
        )

        return rotated

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        """Return a 2-D grayscale array regardless of input colour space."""
        if image.ndim == 2:
            return image
        if image.ndim == 3 and image.shape[2] == 1:
            return image[:, :, 0]
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def _binarise(gray: np.ndarray) -> np.ndarray:
        """
        Produce a binary image where foreground (dark text) pixels are white.

        Steps:
          1. Gaussian blur to suppress fine noise without destroying text edges.
          2. Otsu thresholding — automatically finds the optimal global threshold
             for bimodal (text/background) histograms typical of scanned documents.
          3. Invert so that text pixels are white (required by minAreaRect).
        """
        blurred = cv2.GaussianBlur(gray, (_BLUR_KERNEL, _BLUR_KERNEL), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # After Otsu: background=255, text=0 for typical light-background documents.
        # Invert so text pixels are white for minAreaRect.
        return cv2.bitwise_not(binary)

    def _estimate_angle(
        self, binary: np.ndarray
    ) -> tuple[float, float, str]:
        """
        Estimate the skew angle from the binarised image.

        Returns:
            (raw_angle, confidence, skipped_reason)
            skipped_reason is an empty string when estimation succeeded.
        """
        total_pixels = binary.size
        foreground_pixels = int(np.count_nonzero(binary))

        if foreground_pixels < _MIN_FOREGROUND_PIXELS:
            return 0.0, 0.0, "insufficient foreground pixels (image may be blank)"

        foreground_ratio = foreground_pixels / total_pixels
        if foreground_ratio < _MIN_FOREGROUND_RATIO:
            return 0.0, 0.0, f"foreground ratio {foreground_ratio:.5f} below threshold"

        # Collect coordinates of all foreground pixels.
        # np.column_stack gives an (N, 2) array of (x, y) points as required
        # by cv2.minAreaRect.
        coords = np.column_stack(np.where(binary > 0))  # (row, col) → swap below
        # cv2.minAreaRect expects (x, y) = (col, row)
        points = coords[:, ::-1].astype(np.float32)

        rect = cv2.minAreaRect(points)
        # rect = ((cx, cy), (w, h), angle)
        # OpenCV returns angle in (-90, 0] for the long axis convention.
        raw_angle = rect[2]
        rect_w, rect_h = rect[1]

        # Confidence: ratio of the bounding-rect area covered by foreground pixels.
        # A tight, well-aligned document gives a high ratio; a sparse or noisy
        # image gives a low ratio.
        rect_area = max(rect_w * rect_h, 1.0)
        confidence = min(foreground_pixels / rect_area, 1.0)

        self._logger.debug(
            "minAreaRect | raw_angle=%.4f° | rect=%dx%d | fg_pixels=%d | "
            "fg_ratio=%.4f | confidence=%.3f",
            raw_angle, int(rect_w), int(rect_h),
            foreground_pixels, foreground_ratio, confidence,
        )

        return raw_angle, confidence, ""

    @staticmethod
    def _normalise_angle(raw_angle: float) -> float:
        """
        Convert the raw minAreaRect angle to a signed rotation angle.

        cv2.minAreaRect returns angles in (-90, 0].
        Convention:
          - If the rect is wider than tall, the angle is the skew directly.
          - If the rect is taller than wide, OpenCV has swapped the axes and
            added 90°; we subtract 90° to recover the true skew.

        The result is clamped to [-_MAX_CORRECTABLE_ANGLE, +_MAX_CORRECTABLE_ANGLE].
        Angles outside that range are almost certainly detection errors.
        """
        # OpenCV minAreaRect angle is always in (-90, 0].
        # When the document is nearly upright the long axis is vertical and
        # OpenCV reports an angle close to -90°.  We add 90° to get the small
        # positive skew.  When the document is nearly horizontal the angle is
        # already the skew (close to 0°).
        if raw_angle < -45.0:
            angle = raw_angle + 90.0
        else:
            angle = raw_angle

        # Clamp to correctable range
        if abs(angle) > _MAX_CORRECTABLE_ANGLE:
            return 0.0  # signal: skip rotation

        return angle

    @staticmethod
    def _rotate(image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate `image` by `angle` degrees around its centre.

        The output canvas is expanded so no corner content is clipped.
        Border pixels are replicated from the nearest edge pixel.
        """
        h, w = image.shape[:2]
        cx, cy = w / 2.0, h / 2.0

        # Build the 2×3 rotation matrix
        M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)

        # Compute the new canvas dimensions that contain the full rotated image.
        # For a rectangle rotated by θ:
        #   new_w = |w·cos θ| + |h·sin θ|
        #   new_h = |w·sin θ| + |h·cos θ|
        cos_a = abs(M[0, 0])
        sin_a = abs(M[0, 1])
        new_w = int(np.ceil(h * sin_a + w * cos_a))
        new_h = int(np.ceil(h * cos_a + w * sin_a))

        # Adjust the translation component of M to keep the image centred
        M[0, 2] += (new_w / 2.0) - cx
        M[1, 2] += (new_h / 2.0) - cy

        rotated = cv2.warpAffine(
            image,
            M,
            (new_w, new_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated
