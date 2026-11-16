"""
Noise Analyzer.

Estimates global image noise to detect excessively grainy or artificially smoothed scans.
"""

from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_analyzer import BaseImageAnalyzer, ImageAnalysisCache, ImageAnalyzerConfig

class NoiseAnalyzer(BaseImageAnalyzer):
    @property
    def name(self) -> str:
        return "noise_analyzer"

    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # Estimate noise via Median Absolute Deviation (MAD) on Laplacian
        # Laplacian responds strongly to noise.
        median = np.median(cache.laplacian)
        mad = np.median(np.abs(cache.laplacian - median))
        
        # Convert MAD to standard deviation estimate (approx for Gaussian)
        sigma = 1.4826 * mad
        
        if sigma > config.noise_threshold_high:
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.IMAGE,
                severity=60.0,
                description=f"Page {image_index+1} exhibits unusually high noise (sigma: {sigma:.1f}). Possible artificial noise added to hide tampering.",
                source=EvidenceSource.IMAGE,
                recommendation="Review document visually for spliced elements masked by grain."
            ))
        elif sigma < config.noise_threshold_low:
             evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.IMAGE,
                severity=40.0,
                description=f"Page {image_index+1} is suspiciously smooth (sigma: {sigma:.1f}). Possible digital generation or heavy smoothing applied.",
                source=EvidenceSource.IMAGE,
                recommendation="Check if document is a true scan or digitally rendered."
            ))
                
        return evidence
