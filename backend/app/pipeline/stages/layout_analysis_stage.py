"""Layout Analysis Stage — Coordinates structural and typographic layout analysis."""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.layout.layout_service import LayoutService


class LayoutAnalysisStage(BaseStage):
    name = "layout"

    async def run(self, context: AnalysisContext) -> StageResult:
        warnings = []
        if context.ocr_result is None:
            context.structured_document = None
            msg = "Layout analysis skipped: OCR text extraction was unavailable."
            return StageResult.success(self.name, warnings=[msg])

        try:
            service = LayoutService()
            service.process(context)
            if context.structured_document is None:
                warnings.append("Layout analysis produced no structured document.")
            return StageResult.success(self.name, warnings=warnings)
        except Exception as exc:
            msg = f"Layout analysis encountered an issue: {str(exc)}"
            context.add_warning(msg)
            return StageResult.success(self.name, warnings=[msg])

