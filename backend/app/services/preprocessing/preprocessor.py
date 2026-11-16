"""
PreprocessingService — orchestrates image preprocessing for all pages in a document.

Flow per page:
  1. Load image from disk (cv2)
  2. QualityAnalyzer  → QualityMetrics
  3. DecisionEngine   → list[BaseOperation]
  4. Execute each operation via BaseOperation.run()
  5. ArtifactManager  → save result + register Artifact
  6. Populate AnalysisContext and return StageResult
"""

from __future__ import annotations

from pathlib import Path

import cv2

from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.preprocessing.models import QualityMetrics, PreprocessingSummary
from app.services.preprocessing.quality_analyzer import QualityAnalyzer
from app.services.preprocessing.decision_engine import DecisionEngine
from app.services.preprocessing.artifact_manager import ArtifactManager
from app.services.preprocessing.operations import OperationRegistry, build_default_registry
from app.core.logging import get_logger

logger = get_logger(__name__)

_STAGE = "preprocessing"


class PreprocessingService:
    """
    Orchestrates per-page image preprocessing.

    Args:
        output_dir:  Base directory for processed artifacts.
                     ArtifactManager will create a per-document subdirectory.
        registry:    OperationRegistry to use. Defaults to the standard registry.
    """

    def __init__(
        self,
        output_dir: Path,
        registry: OperationRegistry | None = None,
    ) -> None:
        self._output_dir = output_dir
        self._registry = registry or build_default_registry()
        self._analyzer = QualityAnalyzer()
        self._engine = DecisionEngine(self._registry)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def process(self, context: AnalysisContext) -> StageResult:
        """
        Preprocess all pages in context.page_images.

        Reads page paths from context, runs the full preprocessing pipeline
        per page, writes results back to context, and returns a StageResult.
        """
        if not context.page_images:
            return StageResult.success(
                _STAGE,
                warnings=["No page images to preprocess"],
                metadata={"pages_processed": 0},
            )

        artifact_manager = ArtifactManager(
            self._output_dir / context.document_id
        )

        all_metrics: list[QualityMetrics] = []
        summaries: list[PreprocessingSummary] = []
        artifact_ids: list[str] = []
        all_warnings: list[str] = []

        for page_index, page_path in enumerate(context.page_images):
            metrics, summary, warnings = self._process_page(
                page_path=page_path,
                page_index=page_index,
                context=context,
                artifact_manager=artifact_manager,
            )
            all_metrics.append(metrics)
            summaries.append(summary)
            artifact_ids.extend([summary.artifact_id] if summary.artifact_id else [])
            all_warnings.extend(warnings)

        # Store on context
        context.quality_metrics = all_metrics
        context.preprocessing_summary = summaries

        # Populate preprocessed_images from registered artifacts
        context.preprocessed_images = [
            a.path
            for a in context.get_artifact_by_type("preprocessed_image")
        ]

        ops_selected = list({op for s in summaries for op in s.operations_selected})
        ops_executed = list({op for s in summaries for op in s.operations_executed})

        logger.info(
            "Preprocessing complete | job=%s | pages=%d | ops_selected=%s | ops_executed=%s",
            context.job_id,
            len(context.page_images),
            ops_selected,
            ops_executed,
        )

        return StageResult.success(
            _STAGE,
            artifact_ids=artifact_ids,
            warnings=all_warnings,
            metadata={
                "pages_processed": len(context.page_images),
                "operations_selected": ops_selected,
                "operations_executed": ops_executed,
                "quality_score": None,  # Phase 3 placeholder
            },
        )

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _process_page(
        self,
        page_path: str,
        page_index: int,
        context: AnalysisContext,
        artifact_manager: ArtifactManager,
    ) -> tuple[QualityMetrics, PreprocessingSummary, list[str]]:
        warnings: list[str] = []

        # Load image
        image = cv2.imread(page_path)
        if image is None:
            msg = f"Could not load page image: {page_path}"
            logger.warning(msg)
            warnings.append(msg)
            return (
                QualityMetrics(warnings=[msg]),
                PreprocessingSummary(page_index=page_index),
                warnings,
            )

        size_bytes = Path(page_path).stat().st_size if Path(page_path).exists() else 0

        # Quality analysis
        metrics = self._analyzer.analyze(image, size_bytes=size_bytes)
        warnings.extend(metrics.warnings)

        # Operation selection
        operations = self._engine.select(metrics)
        selected_names = [op.name for op in operations]

        # Execute operations
        executed_names: list[str] = []
        current_image = image
        for op in operations:
            current_image, op_warnings = op.run(current_image, context)
            warnings.extend(op_warnings)
            if not op_warnings:
                executed_names.append(op.name)

        # Save and register artifact
        artifact = artifact_manager.save_and_register(
            image=current_image,
            context=context,
            page_index=page_index,
        )

        summary = PreprocessingSummary(
            page_index=page_index,
            operations_selected=selected_names,
            operations_executed=executed_names,
            quality_score=None,  # Phase 3 placeholder
            artifact_id=artifact.id,
        )

        return metrics, summary, warnings
