"""
ORB Feature Analyzer.

Extracts ORB keypoints and generates descriptors.
"""
from typing import List

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class ORBFeatureAnalyzer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "orb_feature_analyzer"

    def analyze(
        self,
        cache: CopyMoveAnalysisCache,
        features: CopyMoveFeatures,
        context: AnalysisContext,
        config: CopyMoveAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        evidence = []
        
        kps, descs = cache.get_orb(scale)
        if kps:
            # We track the max across scales just for summary metrics
            features.keypoint_count_orb = max(features.keypoint_count_orb, len(kps))
            
        return evidence
