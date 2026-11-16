"""
Blur Analyzer.

Computes blur via Variance of Laplacian method.
"""

from typing import List
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_analyzer import BaseImageAnalyzer, ImageAnalysisCache, ImageAnalyzerConfig

class BlurAnalyzer(BaseImageAnalyzer):
    @property
    def name(self) -> str:
        return "blur_analyzer"

    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # Calculate variance of laplacian
        variance = np.var(cache.laplacian)
        
        if variance < config.blur_threshold:
            # Map variance directly to severity. 
            # If threshold is 100, variance 0 = 100 severity, variance 90 = 10 severity.
            severity = max(0.0, min(100.0, 100.0 * (1.0 - (variance / config.blur_threshold))))
            
            if severity > 20: # Only flag if notably blurry
                evidence.append(Evidence(
                    detector=self.name,
                    category=EvidenceCategory.IMAGE,
                    severity=severity,
                    description=f"Page {image_index+1} is heavily blurred (score: {variance:.1f} < {config.blur_threshold})",
                    source=EvidenceSource.IMAGE,
                    recommendation="Ask user to re-scan. High risk of poor OCR or obfuscation."
                ))
                
        return evidence
