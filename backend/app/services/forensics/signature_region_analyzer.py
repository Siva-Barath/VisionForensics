"""
Signature Region Analyzer.

Acts as an orchestrator for multiple internal CV-based signature analyzers.
"""

from typing import List
import cv2
import logging
import math

from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence

from .signature_analyzers import (
    SignatureAnalyzerConfig,
    SignatureAnalysisCache,
    SignatureValidator,
    SignatureFeatures,
    StrokeAnalyzer,
    ContourAnalyzer,
    InkDensityAnalyzer,
    SkeletonAnalyzer,
    ConnectedComponentAnalyzer,
    GeometricAnalyzer,
    SignatureQualityAnalyzer
)

logger = logging.getLogger(__name__)

class SignatureRegionAnalyzer(BaseDetector):
    def __init__(self, config: SignatureAnalyzerConfig = None):
        self.config = config or SignatureAnalyzerConfig()
        self.validator = SignatureValidator()
        
        self.analyzers = [
            StrokeAnalyzer(),
            ContourAnalyzer(),
            InkDensityAnalyzer(),
            SkeletonAnalyzer(),
            ConnectedComponentAnalyzer(),
            GeometricAnalyzer(),
            SignatureQualityAnalyzer()
        ]

    @property
    def name(self) -> str:
        return "signature_region_analyzer"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        all_evidence = []
        doc = context.structured_document
        
        if not doc or not context.preprocessed_images:
            return all_evidence
            
        # For simplicity, we just use the first page image
        img_path = context.preprocessed_images[0]
        img = cv2.imread(img_path)
        if img is None:
            return all_evidence
            
        # Find all signature regions
        for sec in doc.get("sections", []):
            if sec.get("region_type") == "SIGNATURE":
                bbox = sec.get("bounding_box")
                if isinstance(bbox, dict):
                    from app.services.ocr.models import BoundingBox
                    bbox = BoundingBox(points=bbox.get("points", []))
                if not bbox or not bbox.points:
                    continue
                    
                # Crop
                # points are [[x1, y1], [x2, y1], [x2, y2], [x1, y2]] roughly
                xs = [p[0] for p in bbox.points]
                ys = [p[1] for p in bbox.points]
                
                x_min, x_max = max(0, int(min(xs))), min(img.shape[1], int(max(xs)))
                y_min, y_max = max(0, int(min(ys))), min(img.shape[0], int(max(ys)))
                
                crop = img[y_min:y_max, x_min:x_max]
                
                # 1. Validation
                is_valid, warn_msg = self.validator.validate(crop)
                if not is_valid:
                    logger.warning("Signature crop invalid: %s", warn_msg)
                    continue
                    
                # 2. Cache building
                cache = SignatureAnalysisCache(crop)
                features = SignatureFeatures()
                
                # 3. Analyze
                for analyzer in self.analyzers:
                    try:
                        ev = analyzer.analyze(cache, features, context, self.config)
                        all_evidence.extend(ev)
                    except Exception as e:
                        logger.error("Analyzer %s failed: %s", analyzer.name, str(e))
                        
                # 4. Compute complexity score
                complexity = 0.0
                if features.skeleton_length: complexity += min(features.skeleton_length / 50.0, 10.0)
                if features.branch_count: complexity += min(features.branch_count, 15.0)
                if features.contour_count: complexity += min(features.contour_count / 2.0, 10.0)
                if features.stroke_width_std: complexity += (features.stroke_width_std * 2.0)
                
                features.complexity_score = complexity
                
                # If exceptionally simple
                if complexity < self.config.complexity_threshold:
                    from app.services.forensics.models import EvidenceCategory, EvidenceSource
                    all_evidence.append(Evidence(
                        detector=self.name,
                        category=EvidenceCategory.SIGNATURE,
                        severity=65.0,
                        description=f"Signature lacks structural complexity (score: {complexity:.1f}). Possible typed font or forged path.",
                        source=EvidenceSource.IMAGE
                    ))

                # Persist features for ML feature extraction (first region wins)
                if context.signature_features is None:
                    from dataclasses import asdict
                    context.signature_features = asdict(features)
                    
        return all_evidence
