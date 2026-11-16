"""
ContrastEnhancementOperation - Adaptive contrast enhancement.

Algorithm Workflow:
-------------------
We use Contrast Limited Adaptive Histogram Equalization (CLAHE) rather than 
Global Histogram Equalization. Global equalization often over-amplifies noise 
in homogeneous regions and washes out details, making it unsuitable for 
documents. CLAHE operates on small local tiles, preventing noise amplification 
by clipping the histogram at a predefined limit.

1. Analysis: Calculate mean brightness and standard deviation (proxy for contrast).
2. Skip: If the image already has high contrast (std dev > 60), we skip to avoid 
   over-enhancement and creating halos around text.
3. Pre-process: Extremely dark images (brightness < 40) get a global brightness 
   boost before CLAHE.
4. Enhancement:
   - For color (BGR), convert to LAB space, apply CLAHE to L-channel only, and 
     convert back to BGR. This preserves chromaticity (colors) perfectly without 
     introducing false color artifacts.
   - For grayscale, apply CLAHE directly.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


class ContrastEnhancementOperation(BaseOperation):
    name = "contrast"
    description = "Adaptively enhances contrast using CLAHE."
    version = "1.0.0"

    def execute(self, image: np.ndarray, context: "AnalysisContext", **kwargs: Any) -> np.ndarray:
        start_time = time.perf_counter()
        
        self._logger.info("ContrastEnhancementOperation started | job=%s", context.job_id)

        working_img = image.copy()

        if context.metadata is None:
            context.metadata = {}

        def _skip(reason: str, b_before: float, c_before: float) -> np.ndarray:
            self._logger.info("Contrast enhancement skipped: %s | job=%s", reason, context.job_id)
            context.metadata.update({
                "contrast_enhancement_applied": False,
                "algorithm_used": "skip",
                "brightness_before": b_before,
                "contrast_before": c_before,
                "processing_time_ms": (time.perf_counter() - start_time) * 1000
            })
            return image.copy()

        # 1. Analysis
        # Get grayscale for analysis
        if len(working_img.shape) == 3 and working_img.shape[2] != 1:
            gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = working_img.squeeze()

        b_before = float(np.mean(gray))
        c_before = float(np.std(gray))
        
        self._logger.debug("Image stats: brightness=%.2f, contrast=%.2f | job=%s", 
                           b_before, c_before, context.job_id)

        # 2. Skip condition
        if c_before > 60.0:
            return _skip("contrast already sufficient", b_before, c_before)

        # 3. Pre-process Dark Images
        if b_before < 40.0:
            self._logger.debug("Image is dark, applying global brightness scaling | job=%s", context.job_id)
            # Scale brightness up slightly
            scale = 80.0 / max(b_before, 1.0)
            working_img = cv2.convertScaleAbs(working_img, alpha=scale, beta=0)
            # Re-evaluate gray
            if len(working_img.shape) == 3 and working_img.shape[2] != 1:
                gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = working_img.squeeze()

        # 4. Enhancement
        clip_limit = 2.5
        tile_grid_size = (8, 8)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        
        algo_used = "clahe_lab" if len(working_img.shape) == 3 and working_img.shape[2] != 1 else "clahe_gray"

        if len(working_img.shape) == 3 and working_img.shape[2] != 1:
            # Color: Apply to L channel of LAB
            lab = cv2.cvtColor(working_img, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            l_channel = clahe.apply(l_channel)
            merged_lab = cv2.merge((l_channel, a_channel, b_channel))
            enhanced_img = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale: Apply directly
            enhanced_img = clahe.apply(working_img.squeeze())

        # 5. Post-Analysis
        if len(enhanced_img.shape) == 3 and enhanced_img.shape[2] != 1:
            gray_after = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
        else:
            gray_after = enhanced_img

        b_after = float(np.mean(gray_after))
        c_after = float(np.std(gray_after))

        processing_time = (time.perf_counter() - start_time) * 1000

        # 6. Metadata
        context.metadata.update({
            "contrast_enhancement_applied": True,
            "algorithm_used": algo_used,
            "clip_limit": clip_limit,
            "tile_grid_size": list(tile_grid_size),
            "brightness_before": b_before,
            "brightness_after": b_after,
            "contrast_before": c_before,
            "contrast_after": c_after,
            "processing_time_ms": processing_time
        })
        
        self._logger.info("Contrast enhancement applied | algo=%s | clip=%.1f | duration=%.1fms | job=%s", 
                          algo_used, clip_limit, processing_time, context.job_id)
                          
        if image.ndim == 3 and image.shape[2] == 1:
            return enhanced_img[:, :, np.newaxis]
        return enhanced_img
