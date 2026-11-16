"""
Conflict Resolver.
"""
from typing import List, Tuple
from app.services.forensics.models import Evidence

class ConflictResolver:
    def resolve(self, evidence_list: List[Evidence]) -> Tuple[float, str]:
        """
        Returns (penalty_multiplier, explanation)
        """
        multiplier = 1.0
        explanation = ""
        
        # Example conflict: Highly authentic logo but extremely poor image forensics
        # This shouldn't happen unless the logo was pasted perfectly onto a noisy background
        has_authentic_logo = any(e.category.name == "LOGO" and e.severity < 20 for e in evidence_list)
        has_bad_image = any(e.category.name == "IMAGE_FORENSICS" and e.severity > 80 for e in evidence_list)
        
        if has_authentic_logo and has_bad_image:
            multiplier = 0.9
            explanation = "Conflict detected: Logo structurally perfect despite severe global image degradation."
            
        return multiplier, explanation
