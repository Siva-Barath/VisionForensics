"""
Configuration for Evidence Fusion.
"""
from enum import Enum
from pydantic import BaseModel
from typing import Dict

class SensitivityProfile(str, Enum):
    STRICT = "STRICT"
    BALANCED = "BALANCED"
    PERMISSIVE = "PERMISSIVE"

class EvidenceFusionConfig(BaseModel):
    profile: SensitivityProfile = SensitivityProfile.BALANCED
    
    # Baseline Weights
    weights_strict: Dict[str, float] = {
        "COPY_MOVE": 0.35,
        "SIGNATURE": 0.25,
        "LOGO": 0.20,
        "OCR": 0.15,
        "IMAGE_FORENSICS": 0.10,
        "LAYOUT": 0.10,
        "CLASSIFICATION": 0.05
    }
    
    weights_balanced: Dict[str, float] = {
        "COPY_MOVE": 0.30,
        "SIGNATURE": 0.22,
        "LOGO": 0.15,
        "OCR": 0.12,
        "IMAGE_FORENSICS": 0.08,
        "LAYOUT": 0.08,
        "CLASSIFICATION": 0.05
    }
    
    weights_permissive: Dict[str, float] = {
        "COPY_MOVE": 0.25,
        "SIGNATURE": 0.15,
        "LOGO": 0.10,
        "OCR": 0.10,
        "IMAGE_FORENSICS": 0.05,
        "LAYOUT": 0.05,
        "CLASSIFICATION": 0.05
    }

    # Verdict thresholds (Posterior Risk -> Verdict)
    thresholds_strict: Dict[str, float] = {
        "FORGED": 0.70,
        "LIKELY_FORGED": 0.50,
        "SUSPICIOUS": 0.30,
        "LIKELY_AUTHENTIC": 0.10
    }
    
    thresholds_balanced: Dict[str, float] = {
        "FORGED": 0.85,
        "LIKELY_FORGED": 0.65,
        "SUSPICIOUS": 0.40,
        "LIKELY_AUTHENTIC": 0.15
    }
    
    thresholds_permissive: Dict[str, float] = {
        "FORGED": 0.90,
        "LIKELY_FORGED": 0.75,
        "SUSPICIOUS": 0.50,
        "LIKELY_AUTHENTIC": 0.20
    }
    
    def get_active_weights(self) -> Dict[str, float]:
        if self.profile == SensitivityProfile.STRICT: return self.weights_strict
        if self.profile == SensitivityProfile.PERMISSIVE: return self.weights_permissive
        return self.weights_balanced

    def get_active_thresholds(self) -> Dict[str, float]:
        if self.profile == SensitivityProfile.STRICT: return self.thresholds_strict
        if self.profile == SensitivityProfile.PERMISSIVE: return self.thresholds_permissive
        return self.thresholds_balanced
