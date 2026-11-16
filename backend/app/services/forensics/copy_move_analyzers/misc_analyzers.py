"""
False Positive Filter and Block Similarity Analyzer placeholders.
"""

from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class FalsePositiveFilter(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "false_positive_filter"

    def analyze(self, cache: CopyMoveAnalysisCache, features: CopyMoveFeatures, context: AnalysisContext, config: CopyMoveAnalyzerConfig, scale: float = 1.0) -> List[Evidence]:
        # Would filter out tables, bullets etc.
        return []

class BlockSimilarityAnalyzer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "block_similarity_analyzer"

    def analyze(self, cache: CopyMoveAnalysisCache, features: CopyMoveFeatures, context: AnalysisContext, config: CopyMoveAnalyzerConfig, scale: float = 1.0) -> List[Evidence]:
        # Would do NCC sliding window if keypoints failed
        return []

class CopyMoveConfidenceEstimator:
    def estimate(self, features: CopyMoveFeatures) -> float:
        if features.duplicate_pairs:
            return features.duplicate_pairs[0].confidence
        return 0.0
