"""
Recommendation Builder.
"""
from typing import List
from app.services.evidence_fusion.models import FinalForensicAssessment

class RecommendationBuilder:
    def build(self, assessment: FinalForensicAssessment) -> List[str]:
        return [f"{r.action}: {r.reason}" for r in assessment.recommendations]
