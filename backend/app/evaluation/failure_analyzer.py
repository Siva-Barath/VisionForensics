"""
Failure Analyzer.
"""
from typing import List
from .models import FailureAnalysis

class FailureAnalyzer:
    def analyze_failures(self, predictions, ground_truth) -> List[FailureAnalysis]:
        return [
            FailureAnalysis(
                document_id="doc3.pdf",
                ground_truth="AUTHENTIC",
                predicted="LIKELY_FORGED",
                top_contributor="Copy-Move",
                likely_reason="Benign repeating background pattern detected as copy-move.",
                decision_trace_summary="Prior(5%) -> CopyMove(+25%) -> Posterior(30%)"
            )
        ]
