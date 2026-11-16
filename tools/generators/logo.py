"""
generators/logo.py

Forgery generator that replaces or overlays a document logo / seal
to simulate institutional forgery.
"""

from __future__ import annotations

import numpy as np


class LogoGenerator:
    """
    Replaces or composites a forged logo / official seal onto the document.

    Forgery type: ``logo``
    """

    name: str = "logo"

    def apply(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
        import cv2
        h, w = image.shape[:2]
        
        r = int(rng.integers(30, 80))
        if w <= 2*r or h <= 2*r:
            return image, {"severity": 0.0}
            
        cx = int(rng.integers(r, w - r))
        cy = int(rng.integers(r, h - r))
        
        out = image.copy()
        
        # Draw a fake "logo"
        cv2.circle(out, (cx, cy), r, (200, 50, 50), -1)
        cv2.rectangle(out, (cx-r//2, cy-r//2), (cx+r//2, cy+r//2), (50, 200, 50), -1)
        
        return out, {"severity": 1.0, "cx": cx, "cy": cy}
