"""
generators/signature.py

Forgery generator that pastes a synthetic or transplanted signature
onto a document image to simulate signature forgery.
"""

from __future__ import annotations

import numpy as np


class SignatureGenerator:
    """
    Overlays a forged or mismatched signature region onto the document.

    Forgery type: ``signature``
    """

    name: str = "signature"

    def apply(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
        import cv2
        h, w = image.shape[:2]
        
        box_w, box_h = 150, 100
        if w <= box_w or h <= box_h:
            return image, {"severity": 0.0}
            
        x = int(rng.integers(0, w - box_w))
        y = int(rng.integers(0, h - box_h))
        
        out = image.copy()
        
        # Generate some random points for a "signature" scribble
        pts = []
        for i in range(10):
            px = x + int(rng.integers(0, box_w))
            py = y + int(rng.integers(0, box_h))
            pts.append([px, py])
            
        pts = np.array(pts, np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Draw the signature
        cv2.polylines(out, [pts], isClosed=False, color=(0, 0, 150), thickness=2)
        
        return out, {"severity": 1.0, "x": x, "y": y}
