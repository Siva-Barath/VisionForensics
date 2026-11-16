"""Legacy scaffold must never advertise invented performance/readiness."""
import pytest
from app.evaluation.evaluation_runner import EvaluationRunner


def test_evaluation_scaffold_does_not_manufacture_benchmark_results():
    with pytest.raises(NotImplementedError, match="fixed performance"):
        EvaluationRunner().run_benchmark()
