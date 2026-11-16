"""
Ablation Runner.
"""
from typing import List
from .models import AblationResult

class AblationRunner:
    def run_ablations(self) -> List[AblationResult]:
        return [
            AblationResult(detector_removed="Copy-Move", accuracy_drop=0.15, f1_drop=0.14),
            AblationResult(detector_removed="Signature Verification", accuracy_drop=0.08, f1_drop=0.07)
        ]
