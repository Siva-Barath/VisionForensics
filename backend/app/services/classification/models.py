"""
Data models for the Document Classification Engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.services.layout.models import DocumentType

@dataclass
class ClassificationEvidence:
    """Explains why a specific DocumentType scored points."""
    feature_name: str
    score_delta: float
    description: str

@dataclass
class ClassificationSummary:
    """Summary of the classification execution."""
    total_features_extracted: int = 0
    processing_time_ms: float = 0.0

@dataclass
class DocumentPrediction:
    """A single prediction with its normalized confidence."""
    document_type: DocumentType
    confidence: float # 0.0 - 1.0
    evidence: List[ClassificationEvidence] = field(default_factory=list)

@dataclass
class ClassificationResult:
    """The final output of the Classification Engine."""
    predicted_type: DocumentType = DocumentType.UNKNOWN
    confidence: float = 0.0
    top_predictions: List[DocumentPrediction] = field(default_factory=list)
    summary: Optional[ClassificationSummary] = None

@dataclass
class ExtractedFeatures:
    """Normalized features extracted from OCR, Layout, and Image extractors."""
    ocr_text_lower: str = ""
    keywords_found: set[str] = field(default_factory=set)
    table_count: int = 0
    field_count: int = 0
    section_count: int = 0
    signature_regions: int = 0
    logo_regions: int = 0
    page_count: int = 0
    aspect_ratio: float = 1.0
