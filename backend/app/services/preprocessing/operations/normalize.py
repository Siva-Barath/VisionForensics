"""
NormalizationOperation - Document image standardization.

Workflow:
---------
1. Validation: Ensures no NaN or Inf values. 
2. Color Space: Preserves color spaces but ensures a consistent channel structure 
   (either 1-channel Grayscale or 3-channel BGR). Alpha channels are removed.
3. Data Type: Ensures output is an 8-bit unsigned integer (uint8) strictly clamped 
   between 0-255.
4. Resolution: Enforces a sane document resolution boundary. Images that are too 
   small are upscaled to improve OCR text definition. Images that are outrageously 
   large are downscaled to prevent pipeline memory exhaustion. Aspect ratio is 
   always preserved.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


class NormalizationOperation(BaseOperation):
    name = "normalize"
    description = "Standardizes document resolution, bit depth, and color space."
    version = "1.0.0"

    # Configuration
    MIN_DIMENSION = 800
    MAX_DIMENSION = 4000

    def execute(self, image: np.ndarray, context: "AnalysisContext", **kwargs: Any) -> np.ndarray:
        start_time = time.perf_counter()
        
        self._logger.info("NormalizationOperation started | job=%s", context.job_id)

        if context.metadata is None:
            context.metadata = {}

        def _skip(reason: str) -> np.ndarray:
            self._logger.info("Normalization skipped: %s | job=%s", reason, context.job_id)
            context.metadata.update({
                "normalization_applied": False,
                "original_resolution": list(image.shape[:2]),
                "normalized_resolution": list(image.shape[:2]),
                "processing_time_ms": (time.perf_counter() - start_time) * 1000
            })
            return image.copy()

        # 1. Validation
        if image.dtype.kind in 'fc':  # Float or complex
            if np.isnan(image).any() or np.isinf(image).any():
                self._logger.warning("Invalid values (NaN/Inf) found in image | job=%s", context.job_id)
                context.add_warning("normalize: image contains invalid values; normalization skipped")
                return _skip("image contains invalid values")
        
        if image.size == 0 or len(image.shape) < 2:
            self._logger.warning("Invalid image dimensions: %s | job=%s", image.shape, context.job_id)
            return _skip("invalid dimensions")

        working_img = image.copy()
        applied = False
        interp_method = "none"
        scale = 1.0
        
        # 2. Color Space / Channel structure
        channels = 1 if len(working_img.shape) == 2 else working_img.shape[2]
        color_space = "grayscale" if channels == 1 else "bgr"
        
        if channels == 4:
            # Strip alpha channel
            working_img = cv2.cvtColor(working_img, cv2.COLOR_BGRA2BGR)
            channels = 3
            color_space = "bgr"
            applied = True
            
        # 3. Data Type (Bit Depth)
        if working_img.dtype != np.uint8:
            if working_img.dtype.kind in 'fc':
                # Assume float image might be 0-1 range if max <= 1.0
                if working_img.max() <= 1.0:
                    working_img = working_img * 255.0
            working_img = np.clip(working_img, 0, 255).astype(np.uint8)
            applied = True

        # 4. Resolution Normalization
        h, w = working_img.shape[:2]
        min_dim = min(h, w)
        max_dim = max(h, w)
        
        if min_dim < self.MIN_DIMENSION:
            scale = self.MIN_DIMENSION / float(min_dim)
            interp = cv2.INTER_CUBIC
            interp_method = "bicubic"
            applied = True
        elif max_dim > self.MAX_DIMENSION:
            scale = self.MAX_DIMENSION / float(max_dim)
            interp = cv2.INTER_AREA
            interp_method = "area"
            applied = True
            
        if scale != 1.0:
            new_w = int(round(w * scale))
            new_h = int(round(h * scale))
            working_img = cv2.resize(working_img, (new_w, new_h), interpolation=interp)

        processing_time = (time.perf_counter() - start_time) * 1000
        
        if not applied:
            return _skip("already normalized")

        # 5. Metadata
        context.metadata.update({
            "normalization_applied": True,
            "color_space": color_space,
            "original_resolution": [h, w],
            "normalized_resolution": list(working_img.shape[:2]),
            "resize_scale": scale,
            "interpolation_method": interp_method,
            "processing_time_ms": processing_time
        })
        
        self._logger.info(
            "Normalization applied | scale=%.3f | method=%s | channels=%d | duration=%.1fms | job=%s", 
            scale, interp_method, channels, processing_time, context.job_id
        )
                          
        return working_img
