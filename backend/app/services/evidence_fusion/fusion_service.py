"""
Evidence Fusion Service Orchestrator.
"""
from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence

from .models import FinalForensicAssessment
from .config import EvidenceFusionConfig
from .evidence_normalizer import EvidenceNormalizer
from .weight_manager import WeightManager
from .dependency_graph import DependencyGraph
from .correlation_analyzer import CorrelationAnalyzer
from .conflict_resolver import ConflictResolver
from .confidence_calibrator import ConfidenceCalibrator
from .bayesian_risk_estimator import BayesianRiskEstimator
from .verdict_generator import VerdictGenerator
from .recommendation_engine import RecommendationEngine
from .detector_health_monitor import DetectorHealthMonitor

class EvidenceFusionService:
    def __init__(self, config: EvidenceFusionConfig = None):
        self.config = config or EvidenceFusionConfig()
        
        self.normalizer = EvidenceNormalizer()
        self.weight_manager = WeightManager(self.config)
        self.dependency_graph = DependencyGraph()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.conflict_resolver = ConflictResolver()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.bayesian_estimator = BayesianRiskEstimator()
        self.verdict_generator = VerdictGenerator()
        self.recommendation_engine = RecommendationEngine()
        self.health_monitor = DetectorHealthMonitor()

    def fuse(self, evidence_list: List[Evidence], context: AnalysisContext) -> FinalForensicAssessment:
        raise NotImplementedError(
            "Legacy Bayesian fusion policy is unvalidated and not registered. "
            "Use the preserved three-track RiskStage; do not substitute an unvalidated calibrated verdict."
        )
