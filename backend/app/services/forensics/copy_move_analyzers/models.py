"""
Models for the Copy-Move Forgery Detection Engine.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from app.services.ocr.models import BoundingBox

class DuplicateType(str, Enum):
    SIGNATURE = "SIGNATURE"
    STAMP = "STAMP"
    TEXT = "TEXT"
    TABLE = "TABLE"
    LOGO = "LOGO"
    UNKNOWN = "UNKNOWN"

@dataclass
class DuplicateRegionPair:
    source_bbox: BoundingBox
    dest_bbox: BoundingBox
    duplicate_type: DuplicateType = DuplicateType.UNKNOWN
    confidence: float = 0.0
    # Additional context
    translation_vector: Optional[tuple[float, float]] = None

@dataclass
class CopyMoveFeatures:
    """Mathematical features extracted during copy-move analysis."""
    keypoint_count_orb: int = 0
    keypoint_count_akaze: int = 0
    
    descriptor_matches: int = 0
    inlier_matches: int = 0
    
    average_region_size: float = 0.0
    average_translation: Optional[tuple[float, float]] = None
    
    duplicate_pairs: List[DuplicateRegionPair] = field(default_factory=list)
    confidence: float = 0.0
