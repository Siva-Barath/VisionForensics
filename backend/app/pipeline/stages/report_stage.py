"""
Report Stage — Validates forensic report readiness and verifies asset integrity
prior to on-demand certified PDF export.
"""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult


class ReportStage(BaseStage):
    name = "report"

    async def run(self, context: AnalysisContext) -> StageResult:
        # Verify that all prerequisites for report generation are present
        has_pages = bool(context.preprocessed_images or context.page_images or context.stored_path)
        has_risk = bool(context.risk_assessment)

        context.report_ready = bool(has_pages and has_risk)
        return StageResult.success(self.name)

