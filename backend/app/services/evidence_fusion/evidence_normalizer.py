"""
Evidence Normalizer.
"""
from typing import List, Dict
from app.services.forensics.models import Evidence

class EvidenceNormalizer:
    def normalize(self, evidence_list: List[Evidence]) -> Dict[str, float]:
        """
        Groups evidence by Category and calculates a normalized severity [0.0, 1.0].
        If multiple evidence items exist for a category, we take the max normalized severity.
        """
        normalized_scores = {}
        
        for ev in evidence_list:
            cat = ev.category.name
            
            # Severity is 0-100. Normalize to 0-1
            base_score = ev.severity / 100.0
            
            # Account for reliability and confidence
            # effective_score = severity * confidence * reliability
            effective_score = base_score * ev.confidence * ev.reliability
            
            if cat not in normalized_scores:
                normalized_scores[cat] = effective_score
            else:
                # Accumulate or max (we use max to prevent lots of tiny anomalies from summing to 1.0 artificially)
                normalized_scores[cat] = max(normalized_scores[cat], effective_score)
                
        return normalized_scores
