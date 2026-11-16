"""
Regression Manager.
"""
from .models import BaselineComparison, EvaluationSummary, PerformanceMetrics

class RegressionManager:
    def compare_with_baseline(self, summary: EvaluationSummary, perf: PerformanceMetrics) -> BaselineComparison:
        return BaselineComparison(
            baseline_version="2.0.0",
            accuracy_delta=0.016, # Example: 95.2 -> 96.8 (+1.6%)
            runtime_delta_ms=-150.0,
            memory_delta_mb=-20.0
        )
