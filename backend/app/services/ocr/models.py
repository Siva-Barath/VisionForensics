"""
Data models for the OCR Framework.

Provides standardized data structures for OCR extraction across all engines.
Ensures downstream components (like post-processing and explainability)
don't need to understand engine-specific outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoundingBox:
    """Represents a bounding box in an image."""
    # We use a list of [x, y] coordinates for polygon flexibility, 
    # but primarily structured as [top_left, top_right, bottom_right, bottom_left]
    points: list[list[int]] = field(default_factory=list)

    @property
    def xmin(self) -> int:
        if not self.points: return 0
        return min(p[0] for p in self.points)

    @property
    def ymin(self) -> int:
        if not self.points: return 0
        return min(p[1] for p in self.points)

    @property
    def xmax(self) -> int:
        if not self.points: return 0
        return max(p[0] for p in self.points)

    @property
    def ymax(self) -> int:
        if not self.points: return 0
        return max(p[1] for p in self.points)


@dataclass
class OCRWord:
    text: str
    confidence: float
    bounding_box: BoundingBox
    rotation_angle: Optional[float] = None


@dataclass
class OCRLine:
    words: list[OCRWord] = field(default_factory=list)
    
    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


@dataclass
class OCRBlock:
    lines: list[OCRLine] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


@dataclass
class OCRPage:
    page_index: int
    blocks: list[OCRBlock] = field(default_factory=list)
    
    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks)


@dataclass
class OCRSummary:
    """Summary metrics of the OCR execution."""
    average_confidence: float = 0.0
    min_confidence: float = 0.0
    max_confidence: float = 0.0
    low_confidence_fraction: float = 0.0
    total_words: int = 0
    engine_used: str = ""
    processing_time_ms: float = 0.0


@dataclass
class OCRResult:
    """Complete output of the OCR phase."""
    pages: list[OCRPage] = field(default_factory=list)
    summary: Optional[OCRSummary] = None

    @property
    def full_text(self) -> str:
        return "\n\n---\n\n".join(page.text for page in self.pages)

