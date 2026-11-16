"""
PipelineManager — orchestrates sequential execution of registered stages.

Responsibilities:
- Skip stages disabled by PipelineConfig
- Execute enabled stages in registration order
- Pass the shared AnalysisContext through every stage
- Collect StageResult from each stage and register it on the context
- Catch StageError (recoverable) — record and continue
- Catch PipelineError (unrecoverable) — halt immediately
- Measure total pipeline execution time
- Emit structured logs at every transition
"""

from __future__ import annotations

import time

from app.pipeline.config import PipelineConfig
from app.pipeline.context import AnalysisContext
from app.pipeline.registry import PipelineRegistry
from app.pipeline.stage_result import StageResult
from app.core.constants import PipelineStatus, DocumentStatus
from app.core.exceptions import PipelineError, StageError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PipelineManager:
    def __init__(
        self,
        registry: PipelineRegistry,
        config: PipelineConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or PipelineConfig.full()

    async def run(self, context: AnalysisContext) -> AnalysisContext:
        """
        Execute all enabled stages sequentially against the given context.

        Always returns the context — never raises — so the caller always
        has access to partial results and error details on failure.
        """
        all_stages = self._registry.get_pipeline()
        active_stages = [s for s in all_stages if self._config.is_enabled(s.name)]
        skipped_names = [s.name for s in all_stages if not self._config.is_enabled(s.name)]

        context.pipeline_status = PipelineStatus.RUNNING
        context.document_status = DocumentStatus.PROCESSING

        logger.info(
            "Pipeline started | job=%s | active=%s | skipped=%s",
            context.job_id,
            [s.name for s in active_stages],
            skipped_names,
        )

        # Register skipped-stage results so consumers have a complete picture
        for name in skipped_names:
            context.register_result(
                StageResult.skipped(name, reason="Disabled by PipelineConfig")
            )

        wall_start = time.perf_counter()

        for stage in active_stages:
            context.current_stage = stage.name
            try:
                # execute() handles timing, logging, and result registration
                await stage.execute(context)
                context.mark_stage_complete(stage.name)

            except StageError as exc:
                # Recoverable — record and continue to next stage
                logger.warning(
                    "Recoverable stage error | stage=%s | job=%s | %s",
                    stage.name, context.job_id, exc.detail,
                )
                context.record_stage_error(stage.name, exc.detail)
                context.register_result(
                    StageResult.failed(stage.name, error=exc.detail)
                )

            except PipelineError as exc:
                # Unrecoverable — halt pipeline immediately
                logger.error(
                    "Pipeline halted | stage=%s | job=%s | %s",
                    stage.name, context.job_id, exc.message,
                )
                context.record_stage_error(stage.name, exc.message)
                context.register_result(
                    StageResult.failed(stage.name, error=exc.message)
                )
                context.pipeline_status = PipelineStatus.FAILED
                context.document_status = DocumentStatus.FAILED
                context.processing_time_ms = (time.perf_counter() - wall_start) * 1000
                return context

            except Exception as exc:
                # Unexpected — treat as unrecoverable
                logger.exception(
                    "Unexpected exception | stage=%s | job=%s",
                    stage.name, context.job_id,
                )
                context.record_stage_error(stage.name, str(exc))
                context.register_result(
                    StageResult.failed(stage.name, error=str(exc))
                )
                context.pipeline_status = PipelineStatus.FAILED
                context.document_status = DocumentStatus.FAILED
                context.processing_time_ms = (time.perf_counter() - wall_start) * 1000
                return context

        context.processing_time_ms = (time.perf_counter() - wall_start) * 1000

        if context.has_error():
            context.pipeline_status = PipelineStatus.PARTIAL
        else:
            context.pipeline_status = PipelineStatus.COMPLETED
            context.document_status = DocumentStatus.PROCESSED

        logger.info(
            "Pipeline finished | job=%s | status=%s | duration=%.1fms | stages=%s",
            context.job_id,
            context.pipeline_status,
            context.processing_time_ms,
            context.completed_stages,
        )

        return context
