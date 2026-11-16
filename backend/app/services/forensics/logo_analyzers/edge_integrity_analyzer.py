"""
Edge Integrity Analyzer.

Detects jagged borders, broken edges, and aliasing.
"""
from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_logo_analyzer import BaseLogoAnalyzer, LogoAnalysisCache, LogoAnalyzerConfig
from .models import LogoFeatures

class EdgeIntegrityAnalyzer(BaseLogoAnalyzer):
    @property
    def name(self) -> str:
        return "edge_integrity_analyzer"

    def analyze(self, cache: LogoAnalysisCache, features: LogoFeatures, context: AnalysisContext, config: LogoAnalyzerConfig, scale: float = 1.0) -> List[Evidence]:
        evidence = []
        
        edges = cache.get_edges(scale)
        binary = cache.get_binary(scale)
        
        edge_pixels = np.count_nonzero(edges)
        total_pixels = edges.shape[0] * edges.shape[1]
        
        density = edge_pixels / total_pixels
        features.edge_density = float(density)
        
        # High edge jaggedness can be detected by looking at the ratio of Canny edges to the contour perimeters
        # A low-res pasted logo scaled up will have very "stair-stepped" edges which create lots of Canny edge pixels.
        
        if scale == 1.0:
            contours = cache.get_contours(scale)
            if contours:
                total_perimeter = sum(cv2.arcLength(c, True) for c in contours)
                if total_perimeter > 0:
                    jaggedness = edge_pixels / total_perimeter
                    
                    if jaggedness > config.edge_jaggedness_threshold * 10:  # arbitrary multiplier for heuristic
                        evidence.append(Evidence(
                            detector=self.name,
                            category=EvidenceCategory.LOGO,
                            severity=40.0,
                            description=f"Logo edges appear highly jagged or aliased. Possible low-resolution insertion or bad scaling.",
                            source=EvidenceSource.IMAGE
                        ))
                        features.authenticity_score -= 15.0
                        
        return evidence
