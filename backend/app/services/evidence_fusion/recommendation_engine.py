"""
Recommendation Engine.
"""
from typing import List
from .models import RiskBreakdown, Recommendation

class RecommendationEngine:
    def generate(self, breakdown: RiskBreakdown) -> List[Recommendation]:
        recs = []
        
        # Sort contributors by risk shift
        sorted_contribs = sorted(breakdown.contributors, key=lambda x: x.risk_shift, reverse=True)
        
        for c in sorted_contribs:
            if c.risk_shift > 0.15: # Arbitrary high shift
                if c.category == "COPY_MOVE":
                    recs.append(Recommendation("Review Duplicate Regions", "Copy-Move algorithms found strong evidence of duplicated image patches."))
                elif c.category == "SIGNATURE":
                    recs.append(Recommendation("Manual Signature Inspection", "Signature exhibits unnatural mathematical properties."))
                elif c.category == "LOGO":
                    recs.append(Recommendation("Inspect Logo Area", "Logo authenticity checks failed. Possible digital insertion."))
                    
        if breakdown.posterior_risk > 0.8:
            recs.append(Recommendation("Reject Document", "Cumulative evidence overwhelmingly points to forgery."))
            
        return recs
