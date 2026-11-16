"""
generators/noise.py

Forgery generator that adds Gaussian noise to a document image to
simulate low-quality scans or deliberate signal degradation.
"""

from __future__ import annotations

import cv2
import numpy as np


def _noise_severity(sigma: float) -> str:
    """Map noise sigma to a human-readable severity label."""
    if sigma >= 20.0:
        return "high"
    if sigma >= 12.0:
        return "medium"
    return "low"


class NoiseGenerator:
    """
    Adds zero-mean Gaussian noise sampled at a random sigma.

    The sigma is drawn uniformly from ``config.noise_sigma_range``.
    The result is clipped to [0, 255] and cast back to uint8.

    Forgery type: ``noise``
    """

    name: str = "noise"

    def apply(
        self,
        image: np.ndarray,
        rng: np.random.Generator,
        noise_sigma_range: tuple[float, float] = (5.0, 30.0),
    ) -> tuple[np.ndarray, dict]:
        """
        Apply Gaussian noise forgery to *image*.

        Args:
            image:             Source image as a BGR uint8 numpy array.
            rng:               Seeded numpy random Generator.
            noise_sigma_range: (min, max) sigma bounds.

        Returns:
            Tuple of (forged_image, metadata).
        """
        lo, hi = noise_sigma_range
        sigma = float(rng.uniform(lo, hi))

        noise = rng.normal(loc=0.0, scale=sigma, size=image.shape)
        forged = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        metadata = {
            "sigma": round(sigma, 3),
            "severity": _noise_severity(sigma),
        }
        return forged, metadata
