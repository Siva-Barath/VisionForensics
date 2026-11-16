"""
PreprocessingStage — pipeline stage that drives image preprocessing.

Responsibilities:
  1. Convert PDF → page images via PDFService (unchanged from Phase 1)
  2. Delegate all image preprocessing to PreprocessingService

No business logic lives here. The stage is a thin adapter between the
pipeline and the preprocessing subsystem.
"""

from __future__ import annotations

from pathlib import Path

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.pipeline.artifact import Artifact
from app.core.exceptions import StageError, PipelineError


class PreprocessingStage(BaseStage):
    name = "preprocessing"

    def __init__(self, pdf_service, preprocessing_service) -> None:  # type: ignore[annotation]
        super().__init__()
        self._pdf = pdf_service
        self._preprocessing = preprocessing_service

    async def run(self, context: AnalysisContext) -> StageResult:
        # ------------------------------------------------------------------ #
        # Step 1 — resolve page images (PDF conversion or direct image path)  #
        # ------------------------------------------------------------------ #
        if context.file_type != "pdf":
            if context.stored_path:
                context.page_images = [str(context.stored_path)]
                context.page_count = 1
        else:
            if context.stored_path is None:
                raise StageError(self.name, "stored_path is not set — UploadStage must run first")
            try:
                page_paths = self._pdf.convert(
                    pdf_path=context.stored_path,
                    document_id=context.document_id,
                )
                context.page_images = page_paths
                context.page_count = len(page_paths)
            except Exception as exc:
                # No later stage may analyze missing or synthetic PDF pixels.
                raise PipelineError(self.name, "PDF page rendering failed; no forensic analysis was performed") from exc

            # Register raw page images as artifacts
            for i, path in enumerate(context.page_images):
                context.register_artifact(Artifact(
                    type="page_image",
                    path=path,
                    mime_type="image/png",
                    created_by_stage=self.name,
                    page_index=i,
                ))

        # ------------------------------------------------------------------ #
        # Step 2 — preprocess page images                                     #
        # ------------------------------------------------------------------ #
        return self._preprocessing.process(context)
