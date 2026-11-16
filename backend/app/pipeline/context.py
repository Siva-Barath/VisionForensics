"""
AnalysisContext — the single shared state object that flows through every pipeline stage.

Every stage reads from and writes to this object. No stage passes data directly to another.
Adding a new forensic module means adding new fields here and a new stage class — nothing else changes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from app.pipeline.stage_result import StageResult
    from app.pipeline.artifact import Artifact
    from app.services.preprocessing.models import QualityMetrics, PreprocessingSummary


@dataclass
class AnalysisContext:
    # ------------------------------------------------------------------ #
    # Identity                                                             #
    # ------------------------------------------------------------------ #
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------ #
    # Input                                                                #
    # ------------------------------------------------------------------ #
    original_filename: str = ""
    file_type: str = ""          # pdf | png | jpeg
    file_bytes: bytes = field(default=b"", repr=False)
    size_bytes: int = 0

    # ------------------------------------------------------------------ #
    # Storage (set by UploadStage)                                         #
    # ------------------------------------------------------------------ #
    stored_path: Optional[Path] = None

    # ------------------------------------------------------------------ #
    # Preprocessing (set by PreprocessingStage)                            #
    # ------------------------------------------------------------------ #
    page_images: list[str] = field(default_factory=list)   # paths to raw page PNGs
    page_count: Optional[int] = None
    preprocessed_images: list[str] = field(default_factory=list)
    # Per-page quality measurements collected by QualityAnalyzer
    quality_metrics: list["QualityMetrics"] = field(default_factory=list)
    # Per-page record of what the preprocessing stage decided and executed
    preprocessing_summary: list["PreprocessingSummary"] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # OCR (Phase 2)                                                        #
    # ------------------------------------------------------------------ #
    ocr_result: Optional[dict[str, Any]] = None
    ocr_summary: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Layout Analysis (Phase 4)                                            #
    # ------------------------------------------------------------------ #
    structured_document: Optional[dict[str, Any]] = None
    layout_summary: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Metadata (Phase 2)                                                   #
    # ------------------------------------------------------------------ #
    metadata: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Document classification (Phase 8)                                    #
    # ------------------------------------------------------------------ #
    document_type: Optional[str] = None   # e.g. "PASSPORT", "INVOICE", "MARKSHEET"
    classification_result: Optional[dict[str, Any]] = None
    document_profile: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Forgery detection (Phase 5)                                          #
    # ------------------------------------------------------------------ #
    evidence_report: Optional[dict[str, Any]] = None
    forgery_report: Optional[dict[str, Any]] = None
    risk_assessment: Optional[dict[str, Any]] = None
    detected_regions: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # ML feature surfaces — set by detectors, consumed by FeatureExtractor #
    # ------------------------------------------------------------------ #
    # Per-page image forensics scalars (blur, noise, ELA, edge, etc.)
    # Shape: list[dict[str, float]], one entry per preprocessed page.
    image_forensics_metrics: list[dict[str, Any]] = field(default_factory=list)

    # SignatureFeatures dataclass serialised to dict (first detected region).
    signature_features: Optional[dict[str, Any]] = None

    # LogoFeatures dataclass serialised to dict (first detected region).
    logo_features: Optional[dict[str, Any]] = None

    # CopyMoveFeatures dataclass serialised to dict (aggregated across pages).
    copy_move_features: Optional[dict[str, Any]] = None
    copy_move_features_by_page: dict[int, dict[str, Any]] = field(default_factory=dict)

    # Per-page ML inference summaries (Stage 1 REM-01)
    pages_ml: list[dict[str, Any]] = field(default_factory=list)

    # Independent Visual Evidence Track (Stage 3 REM-03)
    visual_evidence: Optional[dict[str, Any]] = None

    # JPEG Quality Qualification (Stage 4 REM-04)
    compression_qualification: Optional[dict[str, Any]] = None

    # Max Evidence severity per EvidenceCategory, keyed by category name.
    evidence_category_scores: dict[str, float] = field(default_factory=dict)

    # Intermediate scalars from EvidenceFusionService.
    fusion_metrics: Optional[dict[str, Any]] = None

    # Supervised ML Model Prediction (Phase 5)
    ml_prediction: Optional[dict[str, Any]] = None
    # Immutable copy captured before document-level heuristic qualification.
    raw_ml_prediction: Optional[dict[str, Any]] = None
    module_execution: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Risk scoring (Phase 4)                                               #
    # ------------------------------------------------------------------ #
    risk_score: Optional[float] = None       # 0.0 – 1.0
    risk_label: Optional[str] = None         # low | medium | high | critical

    # ------------------------------------------------------------------ #
    # Explainability (Phase 5)                                             #
    # ------------------------------------------------------------------ #
    heatmap_paths: list[str] = field(default_factory=list)
    explanation: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Report (Phase 5)                                                     #
    # ------------------------------------------------------------------ #
    report_path: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Pipeline execution metadata                                          #
    # ------------------------------------------------------------------ #
    current_stage: str = "upload"
    completed_stages: list[str] = field(default_factory=list)
    pipeline_status: str = "pending"   # pending | running | completed | failed | partial
    document_status: str = "uploaded"  # uploaded | processing | processed | failed
    warnings: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)  # stage_name → error message
    processing_time_ms: Optional[float] = None

    # ------------------------------------------------------------------ #
    # Structured stage outputs (Task 2)                                    #
    # ------------------------------------------------------------------ #
    # Ordered list of StageResult objects — one per completed stage.
    # The Risk Engine and Report Generator consume these directly so they
    # remain decoupled from individual stage implementations.
    stage_results: list["StageResult"] = field(default_factory=list)

    # All files generated during pipeline execution, keyed by Artifact.id.
    # Stages register Artifacts here instead of scattering raw paths across fields.
    artifacts: list["Artifact"] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #
    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    document_profile: Optional[str] = None
    
    # Evidence Fusion
    final_assessment: Optional[Any] = None

    def record_stage_error(self, stage: str, message: str) -> None:
        self.errors[stage] = message

    def mark_stage_complete(self, stage: str) -> None:
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.current_stage = stage

    def has_error(self) -> bool:
        return bool(self.errors)

    def register_result(self, result: "StageResult") -> None:
        """Append a StageResult produced by a completed stage."""
        self.stage_results.append(result)

    def register_artifact(self, artifact: "Artifact") -> None:
        """Register a generated file artifact."""
        self.artifacts.append(artifact)

    def get_artifact_by_type(self, artifact_type: str) -> list["Artifact"]:
        """Return all artifacts of a given semantic type."""
        return [a for a in self.artifacts if a.type == artifact_type]

    def get_stage_result(self, stage_name: str) -> Optional["StageResult"]:
        """Return the StageResult for a given stage, or None if not yet run."""
        for r in self.stage_results:
            if r.stage_name == stage_name:
                return r
        return None
