"""
PipelineConfig — controls which stages are active at runtime.

Keeping configuration separate from the registry means the same
PipelineRegistry can be used in different configurations (e.g. a
lightweight "quick scan" profile vs. a full forensic analysis profile)
without changing any stage or service code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from app.core.constants import PIPELINE_STAGE_ORDER


@dataclass
class PipelineConfig:
    """
    Defines which pipeline stages are enabled.

    By default every stage in PIPELINE_STAGE_ORDER is enabled.
    Pass a subset to `enabled_stages` to run a partial pipeline.

    Example — run only upload and preprocessing:
        PipelineConfig(enabled_stages=["upload", "preprocessing"])
    """

    enabled_stages: list[str] = field(
        default_factory=lambda: list(PIPELINE_STAGE_ORDER)
    )

    def is_enabled(self, stage_name: str) -> bool:
        return stage_name in self.enabled_stages

    @classmethod
    def full(cls) -> "PipelineConfig":
        """All stages enabled — default production configuration."""
        return cls()

    @classmethod
    def upload_only(cls) -> "PipelineConfig":
        """Only ingest and store — useful for testing the upload path."""
        return cls(enabled_stages=["upload", "preprocessing"])
