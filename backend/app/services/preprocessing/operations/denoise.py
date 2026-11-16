"""
DenoiseOperation - Adaptive document image denoising.

Algorithm Selection Strategy:
-----------------------------
We estimate the noise characteristics by comparing the original grayscale image
to a 3x3 median-filtered version. The mean absolute difference (MAD) serves as
a proxy for high-frequency noise.
- Low MAD (< 1.0): Clean image. Skip denoising to preserve maximum detail.
- Slight MAD (1.0 - 2.5): Minor compression artifacts or slight noise. Use 
  Bilateral Filter to smooth flat regions while strictly preserving text edges.
- High MAD (> 6.0): Severe impulse noise (salt-and-pepper). Use Median Blur, 
  which is highly effective at removing impulse noise.
- Moderate MAD (2.5 - 6.0): Standard Gaussian/camera noise. Use Fast Non-Local 
  Means Denoising, which removes grain well but is more computationally expensive.

This adaptive strategy ensures we do not over-smooth clean documents or apply 
the wrong filter to impulse noise.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


class DenoiseOperation(BaseOperation):
    name = "denoise"
    description = "Adaptively reduces noise in document images while preserving edges."
    version = "1.0.0"

    def execute(self, image: np.ndarray, context: "AnalysisContext", **kwargs: Any) -> np.ndarray:
        start_time = time.perf_counter()
        
        self._logger.info("DenoiseOperation started | job=%s", context.job_id)

        # Do not modify in-place
        working_img = image.copy()
        
        # Ensure context.metadata exists
        if context.metadata is None:
            context.metadata = {}

        # 1. Grayscale conversion for noise estimation
        if len(working_img.shape) == 3:
            gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = working_img.copy()

        # 2. Estimate noise level using Mean Absolute Difference (MAD) against median filter
        median_filtered = cv2.medianBlur(gray, 3)
        diff = cv2.absdiff(gray, median_filtered)
        mean_diff = float(np.mean(diff))
        
        self._logger.debug("Estimated noise MAD: %.3f | job=%s", mean_diff, context.job_id)

        # 3. Algorithm Selection
        algo_used = "none"
        params_used = {}
        
        if mean_diff < 1.0:
            # Low noise - skip
            algo_used = "skip"
            result_img = working_img
            self._logger.info("Noise level very low, skipping denoising | job=%s", context.job_id)
            
        elif mean_diff > 6.0:
            # Salt-and-pepper / Severe impulse noise
            algo_used = "median_blur"
            ksize = 3 if mean_diff < 15.0 else 5
            params_used = {"ksize": ksize}
            self._logger.info("Detected salt-and-pepper noise, using median blur | ksize=%d | job=%s", ksize, context.job_id)
            result_img = cv2.medianBlur(working_img, ksize)
            
        elif mean_diff < 2.5:
            # Compression artifacts / slight noise -> Bilateral Filter
            algo_used = "bilateral_filter"
            d, sigmaColor, sigmaSpace = 5, 50, 50
            params_used = {"d": d, "sigmaColor": sigmaColor, "sigmaSpace": sigmaSpace}
            self._logger.info("Detected slight noise, using bilateral filter | job=%s", context.job_id)
            
            # Bilateral filter works on 8-bit 1 or 3 channel
            result_img = cv2.bilateralFilter(working_img, d, sigmaColor, sigmaSpace)
            
        else:
            # Moderate Gaussian noise -> Fast Non-Local Means
            algo_used = "fast_nl_means"
            h_val = 10.0
            params_used = {"h": h_val, "templateWindowSize": 7, "searchWindowSize": 21}
            self._logger.info("Detected moderate noise, using Fast NL Means | job=%s", context.job_id)
            
            if len(working_img.shape) == 3:
                result_img = cv2.fastNlMeansDenoisingColored(working_img, None, h_val, h_val, 7, 21)
            else:
                result_img = cv2.fastNlMeansDenoising(working_img, None, h_val, 7, 21)
                
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # 4. Record Metadata
        denoise_applied = (algo_used != "skip")
        context.metadata.update({
            "denoise_applied": denoise_applied,
            "algorithm_used": algo_used,
            "estimated_noise_level": mean_diff,
            "parameters_used": params_used,
            "processing_time_ms": processing_time
        })
        
        self._logger.info("DenoiseOperation completed | applied=%s | algo=%s | duration=%.1fms | job=%s", 
                          denoise_applied, algo_used, processing_time, context.job_id)
                          
        return result_img
