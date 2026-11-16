"""
Ink Density Analyzer.

Measures the proportion of ink vs background.
"""
from typing import List
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class InkDensityAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "ink_density_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        binary = cache.binary
        total_pixels = binary.shape[0] * binary.shape[1]
        ink_pixels = np.count_nonzero(binary)
        
        density = ink_pixels / total_pixels
        features.ink_density = float(density)
        
        # Normally a signature is sparse. Extremely dense means it's likely a block/stamp.
        if density > config.ink_density_high:
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.SIGNATURE,
                severity=50.0,
                description=f"Signature region has abnormally high ink density ({density:.1%}). Likely a logo, stamp, or digital block.",
                source=EvidenceSource.IMAGE
            ))
        elif density < config.ink_density_low:
             evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.SIGNATURE,
                severity=30.0,
                description=f"Signature is very faint or sparse ({density:.1%}).",
                source=EvidenceSource.IMAGE
            ))
            
        return evidence
