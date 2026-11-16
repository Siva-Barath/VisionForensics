"""
ShadowRemovalOperation - Document shadow and uneven illumination removal.

Algorithm Overview:
-------------------
We employ a background estimation technique based on morphological closing.
1. A large morphological closing operation effectively erases dark foreground 
   elements (text, lines, signatures) while preserving the low-frequency 
   background variations (shadows, gradients).
2. The estimated background is smoothed using a Gaussian filter to remove any 
   remaining high-frequency artifacts (like faint text outlines).
3. We compute the standard deviation of this estimated background. If it's low, 
   the illumination is uniform and we skip processing to avoid over-filtering.
4. For correction, we normalize the original image by dividing it by the 
   estimated background (scaled to 0-255). This flattens the illumination 
   without destroying fine details.
5. For color images, the background is estimated from the grayscale version, 
   but the correction is applied to all color channels equally. This preserves 
   original color ratios perfectly while normalizing brightness.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


class ShadowRemovalOperation(BaseOperation):
    name = "shadow"
    description = "Removes shadows and uneven illumination from document images."
    version = "1.0.0"

    def execute(self, image: np.ndarray, context: "AnalysisContext", **kwargs: Any) -> np.ndarray:
        start_time = time.perf_counter()
        
        self._logger.info("ShadowRemovalOperation started | job=%s", context.job_id)

        working_img = image.copy()

        if context.metadata is None:
            context.metadata = {}

        def _skip(reason: str, var_before: float) -> np.ndarray:
            self._logger.info("Shadow removal skipped: %s | job=%s", reason, context.job_id)
            context.metadata.update({
                "shadow_removal_applied": False,
                "algorithm_used": "skip",
                "illumination_variance_before": var_before,
                "illumination_variance_after": var_before,
                "processing_time_ms": (time.perf_counter() - start_time) * 1000
            })
            return image.copy()

        # 1. Grayscale for illumination estimation
        if len(working_img.shape) == 3:
            gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = working_img

        # 2. Dynamic Kernel Size
        # Kernel should be larger than the thickest text stroke, typically 1-2% of min dimension
        h, w = gray.shape
        k_size = max(21, int(min(h, w) * 0.02))
        if k_size % 2 == 0:
            k_size += 1  # ensure odd for Gaussian blur
            
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))

        # 3. Background Estimation
        # Morphological close erases dark text (foreground), leaving the background
        bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Smooth out any residual edges
        bg = cv2.GaussianBlur(bg, (k_size, k_size), 0)

        # 4. Analyze Illumination
        # Variance of the background gives us the illumination unevenness
        var_before = float(np.var(bg))
        self._logger.debug("Illumination variance before: %.2f | kernel=%d | job=%s", 
                           var_before, k_size, context.job_id)

        if var_before < 100.0:
            # Low variance means uniform illumination, no shadow to remove
            return _skip("illumination already uniform", var_before)

        # 5. Correction
        bg_f = bg.astype(np.float32)
        bg_f[bg_f == 0] = 1.0  # Prevent division by zero
        
        img_f = working_img.astype(np.float32)

        if len(working_img.shape) == 3:
            # Expand bg to 3 channels to divide BGR image
            bg_f_3 = cv2.cvtColor(bg_f, cv2.COLOR_GRAY2BGR)
            corrected_f = (img_f / bg_f_3) * 255.0
        else:
            corrected_f = (img_f / bg_f) * 255.0

        corrected = np.clip(corrected_f, 0, 255).astype(np.uint8)

        # 6. Evaluate correction
        if len(corrected.shape) == 3:
            gray_after = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
        else:
            gray_after = corrected
            
        bg_after = cv2.morphologyEx(gray_after, cv2.MORPH_CLOSE, kernel)
        bg_after = cv2.GaussianBlur(bg_after, (k_size, k_size), 0)
        var_after = float(np.var(bg_after))

        processing_time = (time.perf_counter() - start_time) * 1000

        # 7. Metadata
        context.metadata.update({
            "shadow_removal_applied": True,
            "algorithm_used": "morphological_division",
            "illumination_variance_before": var_before,
            "illumination_variance_after": var_after,
            "background_kernel_size": k_size,
            "processing_time_ms": processing_time
        })
        
        self._logger.info("Shadow removal applied | var_before=%.1f | var_after=%.1f | duration=%.1fms | job=%s", 
                          var_before, var_after, processing_time, context.job_id)
                          
        return corrected
