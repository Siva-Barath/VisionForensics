"""
Data models for the Document Layout Analysis Framework.

These models represent the semantic structure of a document after
raw OCR blocks have been grouped, sorted, and classified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from app.services.ocr.models import BoundingBox, OCRWord


class DocumentType(str, Enum):
    """Supported document types for future classification and field extraction."""
    UNKNOWN = "UNKNOWN"
    MARKSHEET = "MARKSHEET"
    DEGREE_CERTIFICATE = "DEGREE_CERTIFICATE"
    TRANSCRIPT = "TRANSCRIPT"
    ID_CARD = "ID_CARD"
    PASSPORT = "PASSPORT"
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"


class RegionType(str, Enum):
    """Semantic classification of a document layout region."""
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    TITLE = "TITLE"
    PARAGRAPH = "PARAGRAPH"
    FIELD = "FIELD"
    TABLE = "TABLE"
    SIGNATURE = "SIGNATURE"
    STAMP = "STAMP"
    LOGO = "LOGO"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


@dataclass
class DocumentProfile:
    """Represents a set of expected fields or behaviors for a given DocumentType."""
    doc_type: DocumentType
    expected_fields: list[str] = field(default_factory=list)
    # Could also contain anchor keywords, expected tables, etc.


@dataclass
class StructuredField:
    """A key-value pair extracted from the document."""
    key: str
    value: str
    key_bbox: Optional[BoundingBox] = None
    value_bbox: Optional[BoundingBox] = None
    confidence: float = 1.0


@dataclass
class StructuredSection:
    """A logical region or paragraph of text."""
    region_type: RegionType = RegionType.UNKNOWN
    text: str = ""
    words: list[OCRWord] = field(default_factory=list)
    bounding_box: Optional[BoundingBox] = None


@dataclass
class StructuredTable:
    """A detected table containing rows of cells."""
    # Simple representation: list of rows, where each row is a list of strings
    rows: list[list[str]] = field(default_factory=list)
    bounding_box: Optional[BoundingBox] = None
    confidence: float = 1.0


@dataclass
class LayoutSummary:
    """Summary metrics of the layout analysis execution."""
    total_sections: int = 0
    total_fields: int = 0
    total_tables: int = 0
    warnings: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class StructuredDocument:
    """The final structured representation of the document."""
    document_type: DocumentType = DocumentType.UNKNOWN
    sections: list[StructuredSection] = field(default_factory=list)
    fields: list[StructuredField] = field(default_factory=list)
    tables: list[StructuredTable] = field(default_factory=list)
    summary: Optional[LayoutSummary] = None

    def get_field(self, key: str) -> Optional[StructuredField]:
        """Helper to safely fetch a field by exact key match."""
        for f in self.fields:
            if f.key == key:
                return f
        return None
