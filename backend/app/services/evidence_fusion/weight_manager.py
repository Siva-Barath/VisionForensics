"""
Weight Manager.
"""
from typing import Dict
from .config import EvidenceFusionConfig

class WeightManager:
    def __init__(self, config: EvidenceFusionConfig):
        self.config = config

    def get_effective_weights(self, evidence_list, dependency_penalties: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculates final effective weight for each category.
        effective_weight = base_weight * max(confidence * reliability) * dependency_penalty
        """
        base_weights = self.config.get_active_weights()
        effective_weights = {}
        
        # We need the max (confidence * reliability) per category
        cat_conf_rel = {}
        for ev in evidence_list:
            cat = ev.category.name
            cr = ev.confidence * ev.reliability
            cat_conf_rel[cat] = max(cat_conf_rel.get(cat, 0.0), cr)
            
        dependency_penalties = dependency_penalties or {}
            
        for cat, base_w in base_weights.items():
            cr = cat_conf_rel.get(cat, 1.0) # If no evidence, assume 1.0 for weight availability
            penalty = dependency_penalties.get(cat, 1.0)
            
            effective_weights[cat] = base_w * cr * penalty
            
        return effective_weights
