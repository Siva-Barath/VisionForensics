"""
Skeleton Analyzer.

Evaluates the thinned skeleton of the signature.
"""
from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource
from .base_signature_analyzer import BaseSignatureAnalyzer, SignatureAnalysisCache, SignatureAnalyzerConfig
from .models import SignatureFeatures

class SkeletonAnalyzer(BaseSignatureAnalyzer):
    @property
    def name(self) -> str:
        return "skeleton_analyzer"

    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        skel = cache.skeleton
        
        # Length is simply number of pixels in skeleton
        features.skeleton_length = float(np.count_nonzero(skel))
        
        # A robust topological analysis would count branch points and endpoints via hit-or-miss transforms.
        # For performance, we can approximate or use a fast convolution for 3x3 neighborhoods.
        
        # Simple kernel to count neighbors
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]])
                           
        # Convert to 0, 1
        skel_bin = (skel / 255).astype(np.uint8)
        neighbors = cv2.filter2D(skel_bin, -1, kernel)
        
        # Points in skeleton with exactly 1 neighbor are endpoints
        endpoints = np.logical_and(skel_bin == 1, neighbors == 1)
        features.endpoint_count = int(np.sum(endpoints))
        
        # Points with >2 neighbors are branches
        branches = np.logical_and(skel_bin == 1, neighbors > 2)
        features.branch_count = int(np.sum(branches))
        
        if features.branch_count == 0 and features.skeleton_length > 100:
             evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.SIGNATURE,
                severity=45.0,
                description="Long signature with 0 branches. Extremely unnatural for human handwriting.",
                source=EvidenceSource.IMAGE
            ))
            
        return evidence
