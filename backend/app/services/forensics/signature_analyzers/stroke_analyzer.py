"""
Stroke Analyzer.

Measures stroke width uniformity to detect digital renditions vs natural pens.
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class StrokeAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "stroke_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # Distance transform to measure stroke thickness
        dist = cv2.distanceTransform(cache.binary, cv2.DIST_L2, 3)
        
        # Skeleton masks the center of strokes, distance transform value at skeleton gives thickness
        stroke_widths = dist[cache.skeleton > 0] * 2.0
        
        if len(stroke_widths) > 0:
            features.stroke_width_mean = float(np.mean(stroke_widths))
            features.stroke_width_std = float(np.std(stroke_widths))
            
            # Very low std dev implies uniform stroke width (e.g. MS Paint, printed font)
            if features.stroke_width_std < config.stroke_uniformity_threshold:
                evidence.append(Evidence(
                    detector=self.name,
                    category=EvidenceCategory.SIGNATURE,
                    severity=70.0,
                    description=f"Signature stroke width is unnaturally uniform (std: {features.stroke_width_std:.2f}). Possible digital insertion or printed signature.",
                    source=EvidenceSource.IMAGE
                ))
        
        return evidence
