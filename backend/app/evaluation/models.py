"""
Models for Evaluation, Benchmarking & Production Readiness.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

@dataclass
class ExperimentMetadata:
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    software_version: str = "2.1.0"
    python_version: str = "3.10"
    os_info: str = "Windows/Linux"
    random_seed: int = 42
    dataset_version: str = "v1.0"
    git_commit_hash: str = "unknown"

@dataclass
class DetectorMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    execution_rate: float
    avg_confidence: float

@dataclass
class EvaluationSummary:
    overall_accuracy: float
    overall_precision: float
    overall_recall: float
    overall_f1: float
    false_positive_rate: float
    false_negative_rate: float
    calibration_error: float

@dataclass
class CrossDocumentMetrics:
    # Key: Category name (e.g. "Signature Replacement", "Passport")
    accuracy_by_category: Dict[str, float] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    total_time_ms: float
    avg_latency_ms: float
    throughput_docs_per_min: float
    memory_peak_mb: float
    stage_breakdown: Dict[str, float] = field(default_factory=dict)

@dataclass
class RobustnessMetrics:
    blur_degradation_pct: float
    noise_degradation_pct: float
    jpeg_degradation_pct: float

@dataclass
class AblationResult:
    detector_removed: str
    accuracy_drop: float
    f1_drop: float

@dataclass
class FailureAnalysis:
    document_id: str
    ground_truth: str
    predicted: str
    top_contributor: str
    likely_reason: str
    decision_trace_summary: str

@dataclass
class BaselineComparison:
    baseline_version: str
    accuracy_delta: float
    runtime_delta_ms: float
    memory_delta_mb: float

@dataclass
class ReadinessScore:
    overall_score_pct: float
    documentation_pct: float
    tests_pct: float
    coverage_pct: float
    configuration_pct: float
    deployment_pct: float
    benchmarking_pct: float

@dataclass
class BenchmarkReport:
    metadata: ExperimentMetadata
    summary: EvaluationSummary
    cross_document_metrics: CrossDocumentMetrics
    detector_metrics: Dict[str, DetectorMetrics]
    performance: PerformanceMetrics
    robustness: RobustnessMetrics
    ablations: List[AblationResult]
    failures: List[FailureAnalysis]
    regression: Optional[BaselineComparison]
    readiness: ReadinessScore
