"""
generators/copy_move.py

Forgery generator that copies a rectangular patch from one region of
a document and pastes it elsewhere to simulate copy-move tampering.
"""

from __future__ import annotations

import numpy as np


class CopyMoveGenerator:
    """
    Copies a patch from the source image and pastes it at a different location.

    Forgery type: ``copy_move``
    """

    name: str = "copy_move"

    def apply(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
        import cv2
        h, w = image.shape[:2]
        
        # Patch size between 50 and 150 pixels
        patch_w = int(rng.integers(50, 150))
        patch_h = int(rng.integers(50, 150))
        
        if patch_w >= w or patch_h >= h:
            return image, {"severity": 0.0}
            
        # Source coordinates
        src_x = int(rng.integers(0, w - patch_w))
        src_y = int(rng.integers(0, h - patch_h))
        
        # Destination coordinates
        dst_x = int(rng.integers(0, w - patch_w))
        dst_y = int(rng.integers(0, h - patch_h))
        
        # Extract patch
        patch = image[src_y:src_y+patch_h, src_x:src_x+patch_w].copy()
        
        # Apply slight blending or feathering if desired, but for now just simple paste
        out = image.copy()
        out[dst_y:dst_y+patch_h, dst_x:dst_x+patch_w] = patch
        
        return out, {"severity": 1.0, "src_x": src_x, "src_y": src_y, "dst_x": dst_x, "dst_y": dst_y}
