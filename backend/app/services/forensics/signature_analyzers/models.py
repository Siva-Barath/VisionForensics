"""
Models for the Signature Verification Engine.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SignatureFeatures:
    """Mathematical features extracted from a signature region."""
    # Stroke analysis
    stroke_width_mean: Optional[float] = None
    stroke_width_std: Optional[float] = None
    
    # Contour analysis
    contour_count: Optional[int] = None
    contour_area: Optional[float] = None
    contour_perimeter: Optional[float] = None
    
    # Ink Density
    ink_density: Optional[float] = None
    foreground_ratio: Optional[float] = None
    
    # Skeleton Analysis
    skeleton_length: Optional[float] = None
    endpoint_count: Optional[int] = None
    branch_count: Optional[int] = None
    
    # Connected Components
    blob_count: Optional[int] = None
    
    # Geometric
    aspect_ratio: Optional[float] = None
    solidity: Optional[float] = None
    eccentricity: Optional[float] = None
    
    # Quality
    contrast: Optional[float] = None
    
    # Aggregated
    complexity_score: Optional[float] = None
