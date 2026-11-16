"""
PipelineRegistry — manages the ordered set of active pipeline stages.

Stages are stored in insertion order. The registry is the single place
where the active pipeline composition is defined. Adding or removing a
forensic module requires only a register/remove call here — no other
file needs to change.
"""

from __future__ import annotations

from app.pipeline.base_stage import BaseStage
from app.core.logging import get_logger

logger = get_logger(__name__)


class PipelineRegistry:
    def __init__(self) -> None:
        self._stages: dict[str, BaseStage] = {}

    def register(self, stage: BaseStage) -> None:
        """Add a stage to the pipeline. Replaces any existing stage with the same name."""
        if stage.name in self._stages:
            logger.warning("Stage '%s' is already registered — replacing", stage.name)
        self._stages[stage.name] = stage
        logger.debug("Registered pipeline stage: %s", stage.name)

    def remove(self, stage_name: str) -> None:
        """Remove a stage by name. No-op if the stage is not registered."""
        if stage_name in self._stages:
            del self._stages[stage_name]
            logger.debug("Removed pipeline stage: %s", stage_name)

    def get_pipeline(self) -> list[BaseStage]:
        """Return the ordered list of registered stages."""
        return list(self._stages.values())

    def stage_names(self) -> list[str]:
        return list(self._stages.keys())

    def __len__(self) -> int:
        return len(self._stages)
