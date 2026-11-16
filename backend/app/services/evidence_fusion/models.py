"""
Models for the Evidence Fusion & Risk Calibration Engine.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class Verdict(str, Enum):
    AUTHENTIC = "AUTHENTIC"
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS"
    LIKELY_FORGED = "LIKELY_FORGED"
    FORGED = "FORGED"

@dataclass
class DetectorHealth:
    detector_name: str
    status: str  # EXECUTED, SKIPPED, FAILED, UNAVAILABLE
    reason: Optional[str] = None

@dataclass
class EvidenceContribution:
    category: str
    base_weight: float
    effective_weight: float
    risk_shift: float  # Percentage shift in the posterior

@dataclass
class RiskBreakdown:
    prior_risk: float
    posterior_risk: float
    contributors: List[EvidenceContribution] = field(default_factory=list)

@dataclass
class Recommendation:
    action: str
    reason: str

@dataclass
class DecisionTraceStep:
    stage: str
    description: str
    value_change: str
    current_posterior: float

@dataclass
class DecisionTrace:
    steps: List[DecisionTraceStep] = field(default_factory=list)

@dataclass
class FinalForensicAssessment:
    verdict: Verdict
    calibrated_risk: float
    breakdown: RiskBreakdown
    recommendations: List[Recommendation] = field(default_factory=list)
    decision_trace: DecisionTrace = field(default_factory=DecisionTrace)
    detector_health: List[DetectorHealth] = field(default_factory=list)
