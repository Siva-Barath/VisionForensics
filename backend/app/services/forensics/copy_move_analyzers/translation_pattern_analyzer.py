"""
Translation Pattern Analyzer.

Analyzes translation vectors of matched keypoints. High clustering of identical vectors implies copy-move.
"""
from typing import List
import numpy as np
from collections import defaultdict

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class TranslationPatternAnalyzer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "translation_pattern_analyzer"

    def analyze(
        self,
        cache: CopyMoveAnalysisCache,
        features: CopyMoveFeatures,
        context: AnalysisContext,
        config: CopyMoveAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        evidence = []
        
        if not hasattr(features, '_temp_matches') or scale not in features._temp_matches:
            return evidence
            
        kps, matches = features._temp_matches[scale]
        
        if len(matches) < config.minimum_match_count:
            return evidence
            
        # Group translations to find rigid shifts
        translations = []
        for m in matches:
            pt1 = np.array(kps[m.queryIdx].pt)
            pt2 = np.array(kps[m.trainIdx].pt)
            
            # Vector from 1 to 2
            vec = pt2 - pt1
            
            # Round to nearest 5 pixels to cluster similar translations naturally
            # (compensates for minor scaling/rotation or noisy keypoints in flat copy-moves)
            rx = round(vec[0] / 5.0) * 5
            ry = round(vec[1] / 5.0) * 5
            
            translations.append((rx, ry))
            
        # Count frequency of each translation
        counts = defaultdict(int)
        for t in translations:
            counts[t] += 1
            
        # Find dominant translations
        if counts:
            best_translation = max(counts.items(), key=lambda x: x[1])
            if best_translation[1] >= config.minimum_match_count:
                # Store the most dominant translation
                features.average_translation = best_translation[0]
                
        return evidence
