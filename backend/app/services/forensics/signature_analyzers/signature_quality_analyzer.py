"""
Signature Quality Analyzer.

Evaluates blur and contrast of the signature crop.
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class SignatureQualityAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "signature_quality_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # Contrast (difference between 95th and 5th percentile)
        p5 = np.percentile(cache.gray, 5)
        p95 = np.percentile(cache.gray, 95)
        
        features.contrast = float(p95 - p5)
        
        return evidence
