"""
BaseStage — abstract base class for every pipeline stage.

To add a new forensic module:
  1. Create a class that inherits from BaseStage
  2. Set `name`, `description`, and optionally `version` / `dependencies`
  3. Implement `run(context)` — read from context, write results back, return StageResult
  4. Register it with PipelineRegistry in app/__init__.py

Nothing else in the codebase needs to change.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.core.logging import get_logger


class BaseStage(ABC):
    """Abstract base class for all pipeline stages."""

    # ------------------------------------------------------------------ #
    # Stage metadata — override in subclasses                             #
    # ------------------------------------------------------------------ #

    #: Canonical stage name — must be unique across the pipeline
    name: str = ""

    #: Human-readable description (appears in reports and debug output)
    description: str = ""

    #: Semantic version of this stage implementation
    version: str = "1.0.0"

    #: Names of stages that must have completed before this stage can run.
    #: PipelineManager uses this for dependency validation (Phase 2+).
    dependencies: list[str] = []

    def __init__(self) -> None:
        if not self.name:
            raise TypeError(f"{self.__class__.__name__} must define a non-empty `name` attribute")
        self._logger = get_logger(f"pipeline.stage.{self.name}")

    # ------------------------------------------------------------------ #
    # Contract                                                             #
    # ------------------------------------------------------------------ #

    @abstractmethod
    async def run(self, context: AnalysisContext) -> StageResult:
        """
        Execute this stage.

        Implementations must:
        - Read required inputs from `context`
        - Write outputs back to `context` (page_images, stored_path, etc.)
        - Register generated files as Artifacts via `context.register_artifact()`
        - Return a StageResult describing the outcome
        - Raise `StageError` for recoverable failures
        - Raise `PipelineError` for unrecoverable failures that must halt the pipeline

        The returned StageResult is automatically registered on the context
        by `execute()` — do not call `context.register_result()` inside `run()`.
        """

    # ------------------------------------------------------------------ #
    # Execution wrapper — called by PipelineManager, do not override      #
    # ------------------------------------------------------------------ #

    async def execute(self, context: AnalysisContext) -> StageResult:
        """
        Wraps `run()` with consistent timing, logging, and result registration.
        PipelineManager calls this method — never `run()` directly.
        """
        self._logger.info(
            "Stage started | stage=%s v%s | job=%s",
            self.name, self.version, context.job_id,
        )
        start = time.perf_counter()

        try:
            result = await self.run(context)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.execution_time_ms = elapsed_ms

            # Propagate stage warnings up to the context warning list
            for warning in result.warnings:
                context.add_warning(warning)

            self._logger.info(
                "Stage completed | stage=%s | job=%s | status=%s | duration=%.1fms | warnings=%d",
                self.name, context.job_id, result.status, elapsed_ms, len(result.warnings),
            )

        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._logger.error(
                "Stage raised exception | stage=%s | job=%s | duration=%.1fms",
                self.name, context.job_id, elapsed_ms,
            )
            raise

        context.register_result(result)
        return result

    # ------------------------------------------------------------------ #
    # Introspection                                                        #
    # ------------------------------------------------------------------ #

    def metadata(self) -> dict:
        """Return a serialisable summary of this stage's metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "dependencies": self.dependencies,
        }
