"""
Correlation Analyzer.
"""
from typing import List
from app.services.forensics.models import Evidence

class CorrelationAnalyzer:
    def analyze(self, evidence_list: List[Evidence]) -> float:
        """
        Returns a correlation multiplier (e.g. 1.2 for synergistic evidence)
        """
        multiplier = 1.0
        cats = {e.category.name for e in evidence_list if e.severity > 50}
        
        # If both CopyMove and Signature are flagged, it's highly synergistic (copied signature)
        if "COPY_MOVE" in cats and "SIGNATURE" in cats:
            multiplier += 0.2
            
        return multiplier
