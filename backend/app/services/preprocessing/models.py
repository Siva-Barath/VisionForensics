"""
Data models for the preprocessing subsystem.

QualityMetrics  — image quality measurements collected before any processing.
PreprocessingSummary — record of what the preprocessing stage decided and executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QualityMetrics:
    """Measurements collected by QualityAnalyzer for a single page image."""

    # ------------------------------------------------------------------ #
    # Dimensions                                                           #
    # ------------------------------------------------------------------ #
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0
    color_channels: int = 0
    size_bytes: int = 0

    # ------------------------------------------------------------------ #
    # Photometric quality                                                  #
    # ------------------------------------------------------------------ #
    # Mean pixel intensity, 0–255 (grayscale equivalent)
    brightness: float = 0.0
    # Standard deviation of pixel intensities — proxy for contrast
    contrast: float = 0.0
    # Laplacian variance — higher = sharper; lower = blurrier
    blur_score: float = 0.0

    # ------------------------------------------------------------------ #
    # Geometric quality (placeholders until Phase 3 algorithms land)      #
    # ------------------------------------------------------------------ #
    # Dominant orientation in degrees (0 = upright). None = not computed.
    orientation: Optional[float] = None
    # Estimated skew angle in degrees. None = not computed.
    skew_angle: Optional[float] = None

    # ------------------------------------------------------------------ #
    # Diagnostics                                                          #
    # ------------------------------------------------------------------ #
    warnings: list[str] = field(default_factory=list)


@dataclass
class PreprocessingSummary:
    """Record of what the preprocessing stage decided and executed per page."""

    page_index: int = 0

    # Names of operations the DecisionEngine selected for this page
    operations_selected: list[str] = field(default_factory=list)

    # Names of operations that were actually executed (subset of selected)
    operations_executed: list[str] = field(default_factory=list)

    # Placeholder quality score — will be derived from QualityMetrics in Phase 3
    quality_score: Optional[float] = None

    # Artifact id of the processed image produced for this page
    artifact_id: Optional[str] = None
