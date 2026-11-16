"""
StageResult — structured output produced by every pipeline stage.

PipelineManager collects these into AnalysisContext.stage_results.
The Risk Engine and Report Generator consume StageResults directly,
so they remain decoupled from individual stage implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StageResult:
    # ------------------------------------------------------------------ #
    # Identity                                                             #
    # ------------------------------------------------------------------ #
    stage_name: str

    # ------------------------------------------------------------------ #
    # Outcome                                                              #
    # ------------------------------------------------------------------ #
    # "success" | "skipped" | "failed"
    status: str = "success"
    execution_time_ms: float = 0.0

    # ------------------------------------------------------------------ #
    # Diagnostics                                                          #
    # ------------------------------------------------------------------ #
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Analysis output                                                      #
    # ------------------------------------------------------------------ #
    # Optional confidence score produced by this stage (0.0 – 1.0).
    # Forensic stages will populate this; infrastructure stages leave it None.
    confidence: Optional[float] = None

    # Paths or references to files produced by this stage.
    # Use Artifact objects (registered on AnalysisContext) rather than raw strings
    # wherever possible — this field holds artifact IDs for cross-referencing.
    artifact_ids: list[str] = field(default_factory=list)

    # Generic key-value store for stage-specific structured output.
    # Keeps StageResult extensible without adding per-stage subclasses.
    metadata: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience constructors                                             #
    # ------------------------------------------------------------------ #
    @classmethod
    def success(
        cls,
        stage_name: str,
        execution_time_ms: float = 0.0,
        *,
        confidence: Optional[float] = None,
        artifact_ids: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        warnings: Optional[list[str]] = None,
    ) -> "StageResult":
        return cls(
            stage_name=stage_name,
            status="success",
            execution_time_ms=execution_time_ms,
            confidence=confidence,
            artifact_ids=artifact_ids or [],
            metadata=metadata or {},
            warnings=warnings or [],
        )

    @classmethod
    def skipped(cls, stage_name: str, reason: str, execution_time_ms: float = 0.0) -> "StageResult":
        return cls(
            stage_name=stage_name,
            status="skipped",
            execution_time_ms=execution_time_ms,
            warnings=[reason],
        )

    @classmethod
    def failed(cls, stage_name: str, error: str, execution_time_ms: float = 0.0) -> "StageResult":
        return cls(
            stage_name=stage_name,
            status="failed",
            execution_time_ms=execution_time_ms,
            errors=[error],
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #
    @property
    def succeeded(self) -> bool:
        return self.status == "success"

    @property
    def was_skipped(self) -> bool:
        return self.status == "skipped"
