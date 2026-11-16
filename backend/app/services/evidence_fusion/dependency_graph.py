"""
Dependency Graph.
Propagates penalties based on evidence relationships (e.g. Blur -> OCR).
"""
from typing import Dict, List
from app.services.forensics.models import Evidence, EvidenceCategory

class DependencyGraph:
    def calculate_penalties(self, evidence_list: List[Evidence]) -> Dict[str, float]:
        penalties = {}
        
        has_blur = any(e.category == EvidenceCategory.IMAGE_FORENSICS and "blur" in e.description.lower() for e in evidence_list)
        
        # If blurry, OCR and Signature reliability takes a hit
        if has_blur:
            penalties["OCR"] = 0.6  # 40% penalty to OCR weight
            penalties["SIGNATURE"] = 0.8
            penalties["LOGO"] = 0.8
            
        return penalties
