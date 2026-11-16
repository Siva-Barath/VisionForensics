"""
generators/blur.py

Forgery generator that applies Gaussian blur to a document image to
obscure tampered regions or degrade forensic evidence.
"""

from __future__ import annotations

import cv2
import numpy as np


def _to_odd(value: int) -> int:
    """Return *value* rounded up to the nearest odd integer (minimum 1)."""
    value = max(1, value)
    return value if value % 2 == 1 else value + 1


def _blur_severity(kernel_size: int) -> str:
    """Map kernel size to a human-readable severity label."""
    if kernel_size >= 11:
        return "high"
    if kernel_size >= 7:
        return "medium"
    return "low"


class BlurGenerator:
    """
    Applies Gaussian blur with a randomly sampled kernel size.

    The kernel size is drawn uniformly from ``config.blur_kernel_range``
    and clamped to the nearest odd integer, as required by OpenCV.

    Forgery type: ``blur``
    """

    name: str = "blur"

    def apply(
        self,
        image: np.ndarray,
        rng: np.random.Generator,
        blur_kernel_range: tuple[int, int] = (3, 15),
    ) -> tuple[np.ndarray, dict]:
        """
        Apply Gaussian blur forgery to *image*.

        Args:
            image:             Source image as a BGR uint8 numpy array.
            rng:               Seeded numpy random Generator.
            blur_kernel_range: (min_px, max_px) kernel size bounds.

        Returns:
            Tuple of (forged_image, metadata).
        """
        lo, hi = blur_kernel_range
        raw_k = int(rng.integers(lo, hi + 1))
        kernel_size = _to_odd(raw_k)

        forged = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigmaX=0)

        metadata = {
            "kernel_size": kernel_size,
            "severity": _blur_severity(kernel_size),
        }
        return forged, metadata
