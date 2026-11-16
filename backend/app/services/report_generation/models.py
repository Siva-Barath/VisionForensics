"""
Models for Professional Forensic Report Generation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

@dataclass
class ReportIntegrity:
    report_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    generation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    software_version: str = ""
    report_hash_sha256: Optional[str] = None
    evidence_hash_sha256: Optional[str] = None
    assets_hash_sha256: Optional[str] = None

@dataclass
class ChainOfCustodyEntry:
    event_time: str
    event_name: str
    operator: str = "SYSTEM"
    notes: str = ""

@dataclass
class TraceabilityEntry:
    evidence_description: str
    detector: str
    region_id: str
    recommendation: str

@dataclass
class ReportValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class RegionSnapshot:
    region_id: str
    detector: str
    severity: float
    confidence: float
    explanation: str
    crop_path: Optional[str] = None
    overlay_path: Optional[str] = None

@dataclass
class EvidenceSummaryEntry:
    detector: str
    severity: float
    confidence: float
    reliability: float
    risk_contribution: float
    status: str

@dataclass
class TechnicalAppendix:
    integrity: ReportIntegrity = field(default_factory=ReportIntegrity)
    chain_of_custody: List[ChainOfCustodyEntry] = field(default_factory=list)
    traceability_matrix: List[TraceabilityEntry] = field(default_factory=list)
    configuration_dump: Dict[str, Any] = field(default_factory=dict)
    detector_health: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class GeneratedReport:
    # Header Info
    document_name: str
    document_type: str
    overall_forgery_risk: float
    final_verdict: str
    confidence: float
    explainability_score: float
    sensitivity_profile: str
    processing_time_ms: float
    
    # Narrative
    investigation_summary: str = ""
    
    # Evidence
    evidence_table: List[EvidenceSummaryEntry] = field(default_factory=list)
    region_snapshots: List[RegionSnapshot] = field(default_factory=list)
    
    # Bayesian Chain
    decision_trace_rendered: str = ""
    
    # Actionable
    recommendations: List[str] = field(default_factory=list)
    
    # Deep dive
    technical_appendix: TechnicalAppendix = field(default_factory=TechnicalAppendix)
    
    # Assets
    asset_paths: Dict[str, str] = field(default_factory=dict)
