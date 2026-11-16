"""
Geometric Consistency Analyzer.

Uses RANSAC to reject random matches and isolate geometrically consistent transformations.
"""
from typing import List
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures

class GeometricConsistencyAnalyzer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "geometric_consistency_analyzer"

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
            
        # Extract location of good matches
        src_pts = np.float32([kps[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kps[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Use RANSAC to find fundamental/homography matrix and reject outliers
        # For copy-move, Affine is often sufficient, but Homography handles rotation/scaling better.
        try:
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, config.ransac_threshold)
        except Exception:
            return evidence
            
        if mask is not None:
            inliers = mask.ravel().tolist()
            inlier_count = sum(inliers)
            
            features.inlier_matches = max(features.inlier_matches, inlier_count)
            
            # Keep only the inliers for clustering
            good_inliers = [matches[i] for i in range(len(matches)) if inliers[i]]
            features._temp_matches[scale] = (kps, good_inliers)
            
        return evidence
