"""
Shape Analyzer.

Computes Hu Moments, convexity, and circularity.
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_logo_analyzer import BaseLogoAnalyzer, LogoAnalysisCache, LogoAnalyzerConfig
from .models import LogoFeatures

class ShapeAnalyzer(BaseLogoAnalyzer):
    @property
    def name(self) -> str:
        return "shape_analyzer"

    def analyze(self, cache: LogoAnalysisCache, features: LogoFeatures, context: AnalysisContext, config: LogoAnalyzerConfig, scale: float = 1.0) -> List[Evidence]:
        evidence = []
        
        # Only compute Hu Moments at the highest resolution for the canonical fingerprint
        if scale == 1.0:
            binary = cache.get_binary(scale)
            moments = cv2.moments(binary)
            
            # Hu Moments are invariant to scale, rotation, and reflection. Very useful for logo fingerprinting.
            hu = cv2.HuMoments(moments)
            # Log transform to make them comparable
            hu_list = []
            for i in range(0, 7):
                if hu[i] != 0:
                    hu_list.append(-1 * np.sign(hu[i]) * np.log10(np.abs(hu[i])))
                else:
                    hu_list.append(0.0)
                    
            features.fingerprint.hu_moments = [float(x[0]) if isinstance(x, np.ndarray) else float(x) for x in hu_list]
            
            # Calculate general shape metrics on the largest contour
            contours = cache.get_contours(scale)
            if contours:
                c = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(c)
                perimeter = cv2.arcLength(c, True)
                
                if perimeter > 0:
                    features.fingerprint.shape_circularity = float(4 * np.pi * area / (perimeter * perimeter))
                    
                hull = cv2.convexHull(c)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    features.fingerprint.solidity = float(area / hull_area)
                    
        return evidence
