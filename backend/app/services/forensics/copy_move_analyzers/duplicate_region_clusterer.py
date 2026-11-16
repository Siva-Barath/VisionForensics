"""
Duplicate Region Clusterer.

Clusters matched inliers into explicit bounding boxes and checks for overlap via IoU.
"""
from typing import List
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.ocr.models import BoundingBox
from app.services.forensics.models import Evidence
from .base_copymove_analyzer import BaseCopyMoveAnalyzer, CopyMoveAnalysisCache, CopyMoveAnalyzerConfig
from .models import CopyMoveFeatures, DuplicateRegionPair

def bb_intersection_over_union(boxA, boxB):
    # box is [xmin, ymin, xmax, ymax]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

class DuplicateRegionClusterer(BaseCopyMoveAnalyzer):
    @property
    def name(self) -> str:
        return "duplicate_region_clusterer"

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
            
        # Very simple global bounding box for the clustered inliers
        # A true production clustering algorithm would use DBSCAN or Agglomerative Clustering
        # on the points to find disjoint copied patches. 
        # Here we demonstrate the bounding box and overlap logic.
        
        xs_src = [kps[m.queryIdx].pt[0] for m in matches]
        ys_src = [kps[m.queryIdx].pt[1] for m in matches]
        
        xs_dst = [kps[m.trainIdx].pt[0] for m in matches]
        ys_dst = [kps[m.trainIdx].pt[1] for m in matches]
        
        src_box = [min(xs_src), min(ys_src), max(xs_src), max(ys_src)]
        dst_box = [min(xs_dst), min(ys_dst), max(xs_dst), max(ys_dst)]
        
        # Ensure we scale the coordinates back to 1.0 scale
        src_box = [coord / scale for coord in src_box]
        dst_box = [coord / scale for coord in dst_box]
        
        # IoU validation
        iou = bb_intersection_over_union(src_box, dst_box)
        if iou > config.overlap_iou_threshold:
            # Overlapping heavily - probably just a dense texture match or same object
            return evidence
            
        # Convert to BoundingBox model
        src_bbox = BoundingBox(points=[
            [src_box[0], src_box[1]],
            [src_box[2], src_box[1]],
            [src_box[2], src_box[3]],
            [src_box[0], src_box[3]]
        ])
        
        dst_bbox = BoundingBox(points=[
            [dst_box[0], dst_box[1]],
            [dst_box[2], dst_box[1]],
            [dst_box[2], dst_box[3]],
            [dst_box[0], dst_box[3]]
        ])
        
        features.duplicate_pairs.append(DuplicateRegionPair(
            source_bbox=src_bbox,
            dest_bbox=dst_bbox,
            translation_vector=features.average_translation,
            confidence=0.85
        ))
        
        features.average_region_size = max(
            features.average_region_size, 
            ((src_box[2] - src_box[0]) * (src_box[3] - src_box[1]))
        )
            
        return evidence
