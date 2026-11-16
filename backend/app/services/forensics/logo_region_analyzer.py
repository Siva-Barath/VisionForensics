"""
Logo Region Analyzer.

Orchestrator for the Logo Verification Engine.
Runs multi-scale analysis and computes the overall Authenticity Score.
"""

from typing import List
import cv2
import logging

from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource

from .logo_analyzers import (
    LogoAnalyzerConfig,
    LogoAnalysisCache,
    LogoValidator,
    LogoFeatures,
    ShapeAnalyzer,
    SymmetryAnalyzer,
    EdgeIntegrityAnalyzer,
    ContourAnalyzer,
    TextureAnalyzer,
    ResolutionAnalyzer,
    GeometricConsistencyAnalyzer,
    ColorConsistencyAnalyzer,
    FeatureDescriptorAnalyzer,
    LogoQualityAnalyzer,
    RegionContextAnalyzer
)

logger = logging.getLogger(__name__)

class LogoRegionAnalyzer(BaseDetector):
    def __init__(self, config: LogoAnalyzerConfig = None):
        self.config = config or LogoAnalyzerConfig()
        self.validator = LogoValidator()
        
        self.analyzers = [
            ShapeAnalyzer(),
            SymmetryAnalyzer(),
            EdgeIntegrityAnalyzer(),
            ContourAnalyzer(),
            TextureAnalyzer(),
            ResolutionAnalyzer(),
            GeometricConsistencyAnalyzer(),
            ColorConsistencyAnalyzer(),
            FeatureDescriptorAnalyzer(),
            LogoQualityAnalyzer(),
            RegionContextAnalyzer()
        ]

    @property
    def name(self) -> str:
        return "logo_region_analyzer"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        all_evidence = []
        doc = context.structured_document
        
        if not doc or not context.preprocessed_images:
            return all_evidence
            
        img_path = context.preprocessed_images[0]
        img = cv2.imread(img_path)
        if img is None:
            return all_evidence
            
        for sec in doc.get("sections", []):
            if sec.get("region_type") == "LOGO":
                bbox = sec.get("bounding_box")
                if isinstance(bbox, dict):
                    from app.services.ocr.models import BoundingBox
                    bbox = BoundingBox(points=bbox.get("points", []))
                if not bbox or not bbox.points:
                    continue
                    
                xs = [p[0] for p in bbox.points]
                ys = [p[1] for p in bbox.points]
                
                x_min, x_max = max(0, int(min(xs))), min(img.shape[1], int(max(xs)))
                y_min, y_max = max(0, int(min(ys))), min(img.shape[0], int(max(ys)))
                
                crop = img[y_min:y_max, x_min:x_max]
                
                is_valid, warn_msg = self.validator.validate(crop)
                if not is_valid:
                    continue
                    
                cache = LogoAnalysisCache(crop)
                features = LogoFeatures()
                
                # Multi-scale loop
                scales = [1.0, 0.75, 0.5]
                
                for scale in scales:
                    for analyzer in self.analyzers:
                        try:
                            ev = analyzer.analyze(cache, features, context, self.config, scale=scale)
                            all_evidence.extend(ev)
                        except Exception as e:
                            logger.error("Logo Analyzer %s failed at scale %s: %s", analyzer.name, scale, str(e))
                            
                # Authenticity Score check
                # Cap the score between 0 and 100
                features.authenticity_score = max(0.0, min(100.0, features.authenticity_score))
                
                if features.authenticity_score < self.config.authenticity_threshold:
                    all_evidence.append(Evidence(
                        detector=self.name,
                        category=EvidenceCategory.LOGO,
                        severity=85.0,
                        description=f"Logo structurally compromised. Low Authenticity Score: {features.authenticity_score:.1f}/100.",
                        source=EvidenceSource.IMAGE
                    ))

                # Persist features for ML feature extraction (first region wins)
                if context.logo_features is None:
                    from dataclasses import asdict
                    context.logo_features = asdict(features)
                    
        return all_evidence
