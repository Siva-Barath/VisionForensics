"""
Connected Component Analyzer.

Analyzes isolated blobs.
"""
from typing import List

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class ConnectedComponentAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "connected_component_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        num_labels, labels, stats, centroids = cache.connected_components
        
        # background is 0, so subtract 1
        features.blob_count = max(0, num_labels - 1)
        
        return evidence
