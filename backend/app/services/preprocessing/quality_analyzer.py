"""
QualityAnalyzer — measures image quality before any preprocessing is applied.

Collects real metrics where OpenCV/NumPy can compute them cheaply.
Orientation and skew detection are placeholders until Phase 3 algorithms land.
Does NOT modify the image.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.services.preprocessing.models import QualityMetrics
from app.core.logging import get_logger

logger = get_logger(__name__)


class QualityAnalyzer:
    """Analyses a single page image and returns a QualityMetrics snapshot."""

    def analyze(self, image: np.ndarray, size_bytes: int = 0) -> QualityMetrics:
        """
        Compute quality metrics for the given image array.

        Args:
            image:      Image loaded as a NumPy array (H×W×C BGR or H×W gray).
            size_bytes: On-disk file size in bytes (pass 0 if unknown).

        Returns:
            QualityMetrics populated with all available measurements.
        """
        warnings: list[str] = []

        if image is None or image.size == 0:
            warnings.append("QualityAnalyzer received an empty image")
            return QualityMetrics(warnings=warnings)

        height, width = image.shape[:2]
        channels = 1 if image.ndim == 2 else image.shape[2]
        aspect_ratio = round(width / height, 4) if height > 0 else 0.0

        # Convert to grayscale for photometric metrics
        if channels == 1:
            gray = image
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        gray_f = gray.astype(np.float32)

        brightness = float(np.mean(gray_f))
        contrast = float(np.std(gray_f))

        # Laplacian variance — higher = sharper
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        logger.debug(
            "Quality metrics | size=%dx%d ch=%d brightness=%.1f contrast=%.1f blur=%.1f",
            width, height, channels, brightness, contrast, blur_score,
        )

        return QualityMetrics(
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            color_channels=channels,
            size_bytes=size_bytes,
            brightness=brightness,
            contrast=contrast,
            blur_score=blur_score,
            orientation=None,   # Phase 3 placeholder
            skew_angle=None,    # Phase 3 placeholder
            warnings=warnings,
        )
