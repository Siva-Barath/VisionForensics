"""
Confidence Calibrator.
"""
from typing import List
from app.services.forensics.models import Evidence

class ConfidenceCalibrator:
    def calibrate(self, evidence_list: List[Evidence], conflict_multiplier: float) -> float:
        base_confidence = 1.0
        
        # Simple heuristic: if we lack fundamental layout data, confidence drops
        has_layout = any(e.category.name == "LAYOUT" for e in evidence_list)
        
        if not has_layout:
            base_confidence *= 0.9
            
        return base_confidence * conflict_multiplier
