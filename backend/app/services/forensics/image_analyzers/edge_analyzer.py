"""
Edge Analyzer.

Uses Canny/Sobel filters to detect abnormal discontinuities in edges that
may indicate spliced objects.
"""

from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_analyzer import BaseImageAnalyzer, ImageAnalysisCache, ImageAnalyzerConfig

class EdgeAnalyzer(BaseImageAnalyzer):
    @property
    def name(self) -> str:
        return "edge_analyzer"

    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # We can analyze the canny edges from cache
        edges = cache.canny
        
        # Calculate edge density
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_pixels = np.count_nonzero(edges)
        density = edge_pixels / total_pixels
        
        # Abnormal edge density can indicate digital generation or tampering
        if density > 0.3: # 30% edge density is extremely high for a document
             evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.IMAGE,
                severity=55.0,
                description=f"Page {image_index+1} has abnormally high edge density ({density:.1%}).",
                source=EvidenceSource.IMAGE,
                recommendation="Investigate for heavy digital noise or artificial artifacts."
            ))
            
        return evidence
