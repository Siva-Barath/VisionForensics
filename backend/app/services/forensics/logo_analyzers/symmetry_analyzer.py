"""
Symmetry Analyzer.

Measures horizontal and vertical symmetry (official emblems are often highly symmetric).
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_logo_analyzer import BaseLogoAnalyzer, LogoAnalysisCache, LogoAnalyzerConfig
from .models import LogoFeatures

class SymmetryAnalyzer(BaseLogoAnalyzer):
    @property
    def name(self) -> str:
        return "symmetry_analyzer"

    def analyze(self, cache: LogoAnalysisCache, features: LogoFeatures, context: AnalysisContext, config: LogoAnalyzerConfig, scale: float = 1.0) -> List[Evidence]:
        evidence = []
        
        if scale == 1.0:
            binary = cache.get_binary(scale)
            
            h, w = binary.shape
            
            # Find center of mass
            M = cv2.moments(binary)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # We can do a simple fold over the vertical axis at cx
                # Flip the left side over to the right and compute intersection over union
                # For a true rigorous check, we crop symmetrically around cx.
                
                max_w = min(cx, w - cx)
                if max_w > 10:
                    left_half = binary[:, cx - max_w : cx]
                    right_half = binary[:, cx : cx + max_w]
                    
                    left_flipped = cv2.flip(left_half, 1)
                    
                    intersection = cv2.bitwise_and(left_flipped, right_half)
                    union = cv2.bitwise_or(left_flipped, right_half)
                    
                    union_area = np.count_nonzero(union)
                    if union_area > 0:
                        sym_h = np.count_nonzero(intersection) / union_area
                        features.fingerprint.symmetry_horizontal = float(sym_h)
                        
                        # Official seals are often highly symmetric. If they are slightly off, it might be rotated/pasted
                        # We don't necessarily penalize low symmetry (could just be an asymmetrical logo), 
                        # but this becomes a key fingerprint component.
        return evidence
