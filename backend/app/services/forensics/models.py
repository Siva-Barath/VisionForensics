"""
Data models for the Forgery Detection Framework.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from app.services.ocr.models import BoundingBox

class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EvidenceCategory(str, Enum):
    METADATA = "METADATA"
    IMAGE = "IMAGE"
    OCR = "OCR"
    LAYOUT = "LAYOUT"
    FIELD = "FIELD"
    SIGNATURE = "SIGNATURE"
    LOGO = "LOGO"
    VISUAL = "VISUAL"
    COPY_MOVE = "COPY_MOVE"
    UNKNOWN = "UNKNOWN"

class EvidenceSource(str, Enum):
    RULE_BASED = "RULE_BASED"
    OCR = "OCR"
    PREPROCESSING = "PREPROCESSING"
    LAYOUT = "LAYOUT"
    IMAGE = "IMAGE"
    ML_MODEL = "ML_MODEL"
    EXTERNAL = "EXTERNAL"

@dataclass
class EvidenceRegion:
    """Bounding box region marking suspicious activity."""
    bounding_box: BoundingBox
    description: str = ""
    page_index: int = 0

@dataclass
class Evidence:
    """A single piece of forensic evidence found by a detector."""
    detector: str
    category: EvidenceCategory
    severity: float  # 0.0 to 100.0, indicating how confident/bad this is
    description: str
    source: EvidenceSource = EvidenceSource.RULE_BASED
    confidence: float = 1.0 # Detection confidence
    reliability: float = 1.0  # Trustworthiness of the evidence (e.g., blurry OCR has low reliability)
    recommendation: str = ""
    regions: List[EvidenceRegion] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page_index: Optional[int] = None

@dataclass
class EvidenceSummary:
    """Aggregated statistics of all evidence collected."""
    total_evidence: int = 0
    highest_severity: float = 0.0
    category_counts: dict[str, int] = field(default_factory=dict)
    source_counts: dict[str, int] = field(default_factory=dict)

@dataclass
class RiskAssessment:
    """Final calculated risk for the document."""
    risk_score: float = 0.0 # 0.0 - 100.0
    risk_label: RiskLevel = RiskLevel.NONE
    contributing_factors: List[str] = field(default_factory=list)

@dataclass
class ForgeryReport:
    """The master report containing all forgery detection outputs."""
    evidence_list: List[Evidence] = field(default_factory=list)
    summary: Optional[EvidenceSummary] = None
    risk_assessment: Optional[RiskAssessment] = None
    processing_time_ms: float = 0.0
