"""
Evaluation Runner / Orchestrator.
"""
import logging
from .models import BenchmarkReport, ExperimentMetadata
from .config import EvaluationConfig
from .dataset_manager import DatasetManager
from .metrics_calculator import MetricsCalculator
from .performance_profiler import PerformanceProfiler
from .robustness_tester import RobustnessTester
from .ablation_runner import AblationRunner
from .failure_analyzer import FailureAnalyzer
from .regression_manager import RegressionManager
from .deployment_validator import DeploymentValidator

logger = logging.getLogger(__name__)

class EvaluationRunner:
    def __init__(self, config: EvaluationConfig = None):
        self.config = config or EvaluationConfig()
        
        self.dataset_manager = DatasetManager()
        self.metrics_calc = MetricsCalculator()
        self.perf_profiler = PerformanceProfiler()
        self.robust_tester = RobustnessTester()
        self.ablation_runner = AblationRunner()
        self.failure_analyzer = FailureAnalyzer()
        self.regression_manager = RegressionManager()
        self.deployment_validator = DeploymentValidator()

    def run_benchmark(self) -> BenchmarkReport:
        raise NotImplementedError(
            "Legacy evaluation scaffold has no verified dataset-driven evaluator. "
            "It must not produce fixed performance or deployment-readiness statistics."
        )
