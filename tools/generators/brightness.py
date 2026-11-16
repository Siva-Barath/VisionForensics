"""
generators/brightness.py

Forgery generator that adjusts the global brightness of a document
image to simulate exposure manipulation or scanner inconsistency.
"""

from __future__ import annotations

import cv2
import numpy as np


def _brightness_severity(alpha: float, beta: float) -> str:
    """
    Map alpha/beta deviation from neutral (alpha=1, beta=0) to severity.

    Uses the combined magnitude of both parameters as a proxy.
    """
    deviation = abs(alpha - 1.0) + abs(beta) / 128.0
    if deviation >= 0.6:
        return "high"
    if deviation >= 0.3:
        return "medium"
    return "low"


class BrightnessGenerator:
    """
    Applies ``dst = clip(alpha * src + beta)`` to alter image brightness.

    - ``alpha`` (contrast/gain) is sampled from ``config.brightness_range``.
    - ``beta``  (bias/offset)   is sampled symmetrically around zero,
      scaled so it cannot push a mid-grey image to pure white or black.

    The result is clipped to [0, 255] via ``cv2.convertScaleAbs`` to
    prevent overexposure and maintain a realistic document appearance.

    Forgery type: ``brightness``
    """

    name: str = "brightness"

    # Maximum absolute beta offset — keeps mid-tones within a realistic range
    _BETA_MAX: float = 60.0

    def apply(
        self,
        image: np.ndarray,
        rng: np.random.Generator,
        brightness_range: tuple[float, float] = (0.5, 1.5),
    ) -> tuple[np.ndarray, dict]:
        """
        Apply brightness forgery to *image*.

        Args:
            image:            Source image as a BGR uint8 numpy array.
            rng:              Seeded numpy random Generator.
            brightness_range: (min, max) alpha (gain) bounds.

        Returns:
            Tuple of (forged_image, metadata).
        """
        lo, hi = brightness_range
        alpha = float(rng.uniform(lo, hi))
        beta = float(rng.uniform(-self._BETA_MAX, self._BETA_MAX))

        # convertScaleAbs saturates at [0, 255] — no manual clip needed
        forged = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        metadata = {
            "alpha": round(alpha, 4),
            "beta": round(beta, 4),
            "severity": _brightness_severity(alpha, beta),
        }
        return forged, metadata
