"""
Descriptor Matcher.

Performs descriptor matching using BFMatcher and Lowe's Ratio Test to find initial correspondences.
"""
from typing import List, Tuple
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class DescriptorMatcher(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "descriptor_matcher"

    def analyze(
        self,
        cache: CopyMoveAnalysisCache,
        features: CopyMoveFeatures,
        context: AnalysisContext,
        config: CopyMoveAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        evidence = []
        
        # We will use AKAZE for robust matching in documents
        kps, descs = cache.get_akaze(scale)
        
        if descs is None or len(kps) < config.minimum_match_count:
            return evidence
            
        # Match descriptors against themselves (finding duplicates within same image)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        
        # k=3 because k=1 is self, k=2 is best match, k=3 is second best match (for Lowe's ratio)
        try:
            matches = bf.knnMatch(descs, descs, k=3)
        except Exception:
            return evidence
            
        good_matches = []
        
        # Apply Lowe's Ratio Test
        for match_set in matches:
            if len(match_set) >= 3:
                m1, m2, m3 = match_set[0], match_set[1], match_set[2]
                
                # m1 is always the keypoint itself (distance 0).
                # We want to check if the best OTHER match (m2) is significantly better than the next best (m3).
                if m1.distance == 0 and m1.trainIdx == m1.queryIdx:
                    if m2.distance < config.ratio_test_threshold * m3.distance:
                        # Also ensure the points aren't physically too close (self-matching a smooth line)
                        pt1 = kps[m1.queryIdx].pt
                        pt2 = kps[m2.trainIdx].pt
                        dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                        
                        if dist > config.cluster_distance:
                            good_matches.append(m2)
                            
        features.descriptor_matches = max(features.descriptor_matches, len(good_matches))
        
        # We store these on the features object temporarily for downstream analyzers
        if not hasattr(features, '_temp_matches'):
            features._temp_matches = {}
        features._temp_matches[scale] = (kps, good_matches)
        
        return evidence
