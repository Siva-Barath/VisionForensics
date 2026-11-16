"""
AKAZE Feature Analyzer.

Extracts AKAZE features (highly robust for scanned docs).
"""
from typing import List

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class AKAZEFeatureAnalyzer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "akaze_feature_analyzer"

    def analyze(
        self,
        cache: CopyMoveAnalysisCache,
        features: CopyMoveFeatures,
        context: AnalysisContext,
        config: CopyMoveAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        evidence = []
        
        kps, descs = cache.get_akaze(scale)
        if kps:
            features.keypoint_count_akaze = max(features.keypoint_count_akaze, len(kps))
            
        return evidence
