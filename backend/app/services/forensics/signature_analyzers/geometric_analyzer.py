"""
Geometric Analyzer.

Computes aspect ratio, convex hull, and solidity.
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class GeometricAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "geometric_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        h, w = cache.original.shape[:2]
        if h > 0:
            features.aspect_ratio = float(w / h)
            
        contours = cache.contours
        if contours:
            # Combine all contours to find a global bounding box/hull for the signature ink
            all_points = np.vstack(contours)
            hull = cv2.convexHull(all_points)
            hull_area = cv2.contourArea(hull)
            
            ink_area = float(features.ink_density * h * w) if features.ink_density else 0
            
            if hull_area > 0:
                features.solidity = float(ink_area / hull_area)
                
            if features.solidity and features.solidity > config.solidity_threshold:
                 evidence.append(Evidence(
                    detector=self.name,
                    category=EvidenceCategory.SIGNATURE,
                    severity=80.0,
                    description=f"Signature is a solid block (solidity: {features.solidity:.2f}). Highly indicative of digital masking or obfuscation.",
                    source=EvidenceSource.IMAGE
                ))
            
        return evidence
