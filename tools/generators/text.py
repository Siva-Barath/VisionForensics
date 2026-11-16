"""
generators/text.py

Forgery generator that alters text fields (name, date, ID number)
on a document image to simulate data tampering.
"""

from __future__ import annotations

import numpy as np


class TextGenerator:
    """
    Overwrites or inpaints text regions with falsified content.

    Forgery type: ``text``
    """

    name: str = "text"

    def apply(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
        import cv2
        h, w = image.shape[:2]
        
        # Draw a text box somewhere in the middle
        box_w, box_h = 200, 50
        if w <= box_w or h <= box_h:
            return image, {"severity": 0.0}
            
        x = int(rng.integers(0, w - box_w))
        y = int(rng.integers(0, h - box_h))
        
        out = image.copy()
        # Create a white background for the text
        cv2.rectangle(out, (x, y), (x + box_w, y + box_h), (255, 255, 255), -1)
        
        # Add some text
        fake_text = "FORGED DATA"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(out, fake_text, (x + 10, y + 35), font, 1.0, (0, 0, 0), 2)
        
        return out, {"severity": 1.0, "x": x, "y": y}
