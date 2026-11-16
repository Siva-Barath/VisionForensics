"""
generators/jpeg.py

Forgery generator that re-encodes a document image at reduced JPEG
quality to introduce compression artefacts consistent with re-saved
tampered documents.
"""

from __future__ import annotations

import cv2
import numpy as np


def _jpeg_severity(quality: int) -> str:
    """Map JPEG quality to a human-readable severity label."""
    if quality < 60:
        return "high"
    if quality < 75:
        return "medium"
    return "low"


class JpegGenerator:
    """
    Re-encodes the image in-memory at a randomly sampled JPEG quality.

    The quality value is drawn uniformly from ``config.jpeg_quality_range``.
    Lower quality → stronger compression artefacts → higher severity.

    Forgery type: ``jpeg``
    """

    name: str = "jpeg"

    def apply(
        self,
        image: np.ndarray,
        rng: np.random.Generator,
        jpeg_quality_range: tuple[int, int] = (50, 85),
    ) -> tuple[np.ndarray, dict]:
        """
        Apply JPEG compression forgery to *image*.

        Args:
            image:              Source image as a BGR uint8 numpy array.
            rng:                Seeded numpy random Generator.
            jpeg_quality_range: (min, max) inclusive quality bounds.

        Returns:
            Tuple of (forged_image, metadata).
        """
        lo, hi = jpeg_quality_range
        quality = int(rng.integers(lo, hi + 1))

        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        ok, buf = cv2.imencode(".jpg", image, encode_params)
        if not ok:
            raise RuntimeError("cv2.imencode failed during JPEG forgery")

        forged = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        metadata = {
            "quality": quality,
            "severity": _jpeg_severity(quality),
            "generator": self.name,
        }
        return forged, metadata
