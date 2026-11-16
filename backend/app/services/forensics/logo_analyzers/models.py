"""
Models for the Logo Verification Engine.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class LogoFingerprint:
    """Canonical mathematical representation of the logo for cross-referencing."""
    hu_moments: Optional[List[float]] = None
    shape_circularity: Optional[float] = None
    shape_compactness: Optional[float] = None
    shape_eccentricity: Optional[float] = None
    
    orb_keypoint_count: int = 0
    orb_descriptor_density: float = 0.0
    
    symmetry_horizontal: Optional[float] = None
    symmetry_vertical: Optional[float] = None
    
    contour_count: int = 0
    contour_complexity: float = 0.0
    
    texture_variance: float = 0.0
    
    aspect_ratio: Optional[float] = None
    solidity: Optional[float] = None
    
    # Store at highest resolution scale
    scale_extracted: float = 1.0

@dataclass
class LogoFeatures:
    """Encapsulates the fingerprint and contextual properties."""
    fingerprint: LogoFingerprint = field(default_factory=LogoFingerprint)
    
    edge_density: float = 0.0
    resolution_quality: float = 0.0
    
    authenticity_score: float = 100.0  # 0 to 100
