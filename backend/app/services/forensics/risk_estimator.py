"""
Risk Estimator.

Configurable weighted scoring system mapping aggregated evidence to a RiskLevel.
"""

from typing import List, Dict
from app.services.forensics.models import Evidence, RiskAssessment, RiskLevel, EvidenceCategory

class RiskEstimator:
    def __init__(self, weights: Dict[EvidenceCategory, float] = None):
        self.weights = weights or {
            EvidenceCategory.METADATA: 15.0,
            EvidenceCategory.IMAGE: 30.0,
            EvidenceCategory.OCR: 15.0,
            EvidenceCategory.LAYOUT: 15.0,
            EvidenceCategory.FIELD: 10.0,
            EvidenceCategory.SIGNATURE: 10.0,
            EvidenceCategory.LOGO: 5.0,
            EvidenceCategory.VISUAL: 10.0,
            EvidenceCategory.UNKNOWN: 5.0
        }
        # Retained after each call so ForgeryService can expose it to AnalysisContext
        self.last_max_severity: Dict[EvidenceCategory, float] = {}

    def estimate(self, evidence_list: List[Evidence]) -> RiskAssessment:
        """
        Calculates normalized risk score (0-100) based on max severity per category
        multiplied by the category weight.
        """
        if not evidence_list:
            return RiskAssessment()
            
        # 1. Find max severity per category
        max_severity_per_cat = {cat: 0.0 for cat in EvidenceCategory}
        
        for ev in evidence_list:
            if ev.severity > max_severity_per_cat[ev.category]:
                max_severity_per_cat[ev.category] = ev.severity

        # Retain for external consumers (e.g. ForgeryService → AnalysisContext)
        self.last_max_severity = max_severity_per_cat
                
        # 2. Compute weighted score
        total_score = 0.0
        total_weight = 0.0
        contributing_factors = []
        
        for cat, weight in self.weights.items():
            max_sev = max_severity_per_cat[cat]
            if max_sev > 0:
                total_score += (max_sev * (weight / 100.0))
                contributing_factors.append(f"{cat.value} ({max_sev:.1f})")
            total_weight += weight
            
        # Normalize in case weights don't sum to 100 perfectly (though they should)
        normalized_score = min(100.0, (total_score / (total_weight / 100.0))) if total_weight > 0 else 0.0
        
        # 3. Map to RiskLevel
        if normalized_score == 0:
            label = RiskLevel.NONE
        elif normalized_score < 25:
            label = RiskLevel.LOW
        elif normalized_score < 50:
            label = RiskLevel.MEDIUM
        elif normalized_score < 75:
            label = RiskLevel.HIGH
        else:
            label = RiskLevel.CRITICAL
            
        return RiskAssessment(
            risk_score=normalized_score,
            risk_label=label,
            contributing_factors=contributing_factors
        )
