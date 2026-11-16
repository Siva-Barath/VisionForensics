"""
Copy-Move Region Analyzer.

Orchestrator for the Copy-Move Forgery Detection Engine.
Runs multi-scale analysis and aggregates evidence.
"""

from typing import List
import cv2
import logging

from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource, EvidenceRegion

from .copy_move_analyzers import (
    CopyMoveAnalyzerConfig,
    CopyMoveAnalysisCache,
    CopyMoveFeatures,
    ORBFeatureAnalyzer,
    AKAZEFeatureAnalyzer,
    DescriptorMatcher,
    TranslationPatternAnalyzer,
    GeometricConsistencyAnalyzer,
    DuplicateRegionClusterer,
    FalsePositiveFilter,
    BlockSimilarityAnalyzer,
    CopyMoveConfidenceEstimator,
    DuplicateType
)

logger = logging.getLogger(__name__)

class CopyMoveRegionAnalyzer(BaseDetector):
    def __init__(self, config: CopyMoveAnalyzerConfig = None):
        self.config = config or CopyMoveAnalyzerConfig()
        
        self.analyzers = [
            ORBFeatureAnalyzer(),
            AKAZEFeatureAnalyzer(),
            DescriptorMatcher(),
            TranslationPatternAnalyzer(),
            GeometricConsistencyAnalyzer(),
            DuplicateRegionClusterer(),
            FalsePositiveFilter(),
            BlockSimilarityAnalyzer()
        ]
        self.estimator = CopyMoveConfidenceEstimator()

    @property
    def name(self) -> str:
        return "copy_move_region_analyzer"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        all_evidence = []
        
        if not context.preprocessed_images:
            return all_evidence
            
        for page_idx, img_path in enumerate(context.preprocessed_images):
            img = cv2.imread(img_path)
            if img is None:
                context.add_warning(f"Copy-move analysis could not read page {page_idx + 1}.")
                continue
                
            cache = CopyMoveAnalysisCache(img)
            features = CopyMoveFeatures()
            
            # Multi-scale loop
            scales = [1.0, 0.75, 0.5, 0.25]
            
            for scale in scales:
                for analyzer in self.analyzers:
                    try:
                        ev = analyzer.analyze(cache, features, context, self.config, scale=scale)
                        all_evidence.extend(ev)
                    except Exception as e:
                        logger.error("CopyMove Analyzer %s failed at scale %s: %s", analyzer.name, scale, str(e))
                        context.add_warning(f"Copy-move analyzer {analyzer.name} failed on page {page_idx + 1}.")
                        
            features.confidence = self.estimator.estimate(features)

            # Serialise per-page copy-move features
            page_serialisable = {
                "keypoint_count_orb": features.keypoint_count_orb,
                "keypoint_count_akaze": features.keypoint_count_akaze,
                "descriptor_matches": features.descriptor_matches,
                "inlier_matches": features.inlier_matches,
                "average_region_size": features.average_region_size,
                "duplicate_pair_count": len(features.duplicate_pairs),
                "confidence": features.confidence,
                "inlier_ratio": (
                    features.inlier_matches / features.descriptor_matches
                    if features.descriptor_matches > 0 else 0.0
                ),
            }
            if hasattr(context, "copy_move_features_by_page"):
                context.copy_move_features_by_page[page_idx] = page_serialisable

            # Persist features for ML — keep the page with highest confidence
            existing = context.copy_move_features
            if existing is None or features.confidence > existing.get("confidence", 0.0):
                context.copy_move_features = page_serialisable
            
            # Classification inference
            doc = context.structured_document
            
            for pair in features.duplicate_pairs:
                if features.confidence > self.config.confidence_threshold:
                    
                    # Layout context inference (Duplicate Type Classification)
                    dup_type = DuplicateType.UNKNOWN
                    
                    if doc and "sections" in doc:
                        for sec in doc["sections"]:
                            rt = sec.get("region_type")
                            bbox = sec.get("bounding_box")
                            if bbox and bbox.points and rt:
                                # basic intersection check
                                xs = [p[0] for p in bbox.points]
                                ys = [p[1] for p in bbox.points]
                                sec_box = [min(xs), min(ys), max(xs), max(ys)]
                                
                                # Compare against pair.source_bbox points
                                pair_xs = [p[0] for p in pair.source_bbox.points]
                                pair_ys = [p[1] for p in pair.source_bbox.points]
                                pair_box = [min(pair_xs), min(pair_ys), max(pair_xs), max(pair_ys)]
                                
                                from .copy_move_analyzers.duplicate_region_clusterer import bb_intersection_over_union
                                if bb_intersection_over_union(sec_box, pair_box) > 0.5:
                                    if rt == "SIGNATURE": dup_type = DuplicateType.SIGNATURE
                                    elif rt == "STAMP": dup_type = DuplicateType.STAMP
                                    elif rt == "LOGO": dup_type = DuplicateType.LOGO
                                    elif rt == "TABLE": dup_type = DuplicateType.TABLE
                                    else: dup_type = DuplicateType.TEXT
                                    break
                                    
                    pair.duplicate_type = dup_type
                    
                    all_evidence.append(Evidence(
                        detector=self.name,
                        category=EvidenceCategory.COPY_MOVE,
                        severity=90.0,
                        description=f"Detected copy-move forgery on Page {page_idx+1}. Duplicated {dup_type.value} region found.",
                        source=EvidenceSource.IMAGE,
                        regions=[
                            EvidenceRegion(bounding_box=pair.source_bbox, description="Source Region", page_index=page_idx),
                            EvidenceRegion(bounding_box=pair.dest_bbox, description="Destination Region", page_index=page_idx)
                        ],
                        page_index=page_idx
                    ))
                    
        return all_evidence
