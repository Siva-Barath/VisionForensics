"""
Contour Analyzer.

Evaluates signature boundaries and complexity.
"""
from typing import List
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class ContourAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "contour_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        contours = cache.contours
        features.contour_count = len(contours)
        
        total_area = sum(cv2.contourArea(c) for c in contours)
        total_perimeter = sum(cv2.arcLength(c, True) for c in contours)
        
        features.contour_area = float(total_area)
        features.contour_perimeter = float(total_perimeter)
        
        # A natural signature usually has a few highly complex contours. 
        # Extremely high contour count might indicate heavy fragmentation or digital noise.
        
        if features.contour_count > config.fragmentation_threshold:
             evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.SIGNATURE,
                severity=60.0,
                description=f"Signature is heavily fragmented into {features.contour_count} parts. Possible poor copy-paste or noise.",
                source=EvidenceSource.IMAGE
            ))
            
        return evidence
