"""
Verdict Generator.
"""
from typing import Dict
from .models import Verdict

class VerdictGenerator:
    def generate(self, posterior_risk: float, thresholds: Dict[str, float]) -> Verdict:
        if posterior_risk >= thresholds.get("FORGED", 0.85):
            return Verdict.FORGED
        if posterior_risk >= thresholds.get("LIKELY_FORGED", 0.65):
            return Verdict.LIKELY_FORGED
        if posterior_risk >= thresholds.get("SUSPICIOUS", 0.40):
            return Verdict.SUSPICIOUS
        if posterior_risk >= thresholds.get("LIKELY_AUTHENTIC", 0.15):
            return Verdict.LIKELY_AUTHENTIC
        return Verdict.AUTHENTIC
