"""
UploadStage — persists the raw file to disk and populates storage fields on the context.

This is the first stage in the pipeline. It delegates all I/O to StorageService
so the stage itself contains zero filesystem logic.
"""

from __future__ import annotations

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.pipeline.artifact import Artifact
from app.core.exceptions import PipelineError


class UploadStage(BaseStage):
    name = "upload"

    def __init__(self, storage_service) -> None:  # type: ignore[annotation]
        super().__init__()
        self._storage = storage_service

    async def run(self, context: AnalysisContext) -> StageResult:
        try:
            stored_path = self._storage.save_upload(
                content=context.file_bytes,
                document_id=context.document_id,
                original_filename=context.original_filename,
            )
            context.stored_path = stored_path
        except Exception as exc:
            raise PipelineError(self.name, str(exc)) from exc

        artifact = Artifact(
            type="original_upload",
            path=str(stored_path),
            mime_type=f"image/{context.file_type}" if context.file_type != "pdf" else "application/pdf",
            created_by_stage=self.name,
        )
        context.register_artifact(artifact)
        return StageResult.success(self.name, artifact_ids=[artifact.id])
