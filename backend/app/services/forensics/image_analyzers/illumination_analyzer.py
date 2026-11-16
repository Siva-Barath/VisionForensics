"""
Illumination Analyzer.

Estimates local illumination gradients to detect localized brightness anomalies.
"""

from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_analyzer import BaseImageAnalyzer, ImageAnalysisCache, ImageAnalyzerConfig

class IlluminationAnalyzer(BaseImageAnalyzer):
    @property
    def name(self) -> str:
        return "illumination_analyzer"

    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # Strong localized illumination changes can be detected via large blur kernels
        # to estimate the background light distribution.
        
        bg_illum = cv2.GaussianBlur(cache.gray, (101, 101), 0)
        
        # Standard deviation of the background illumination
        std_illum = np.std(bg_illum)
        
        if std_illum > config.illumination_std_threshold:
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.IMAGE,
                severity=60.0,
                description=f"Page {image_index+1} has extreme lighting gradients (std: {std_illum:.1f}).",
                source=EvidenceSource.IMAGE,
                recommendation="Check for shadow tampering or flash-splicing."
            ))
            
        return evidence
