"""OCR Stage — Delegates to OCRService if dependencies are available, or marks gracefully unavailable."""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.ocr.ocr_service import OCRService
from app.services.ocr.engine_selector import EngineSelector
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRStage(BaseStage):
    name = "ocr"

    async def run(self, context: AnalysisContext) -> StageResult:
        warnings = []
        try:
            selector = EngineSelector()
            working_engine = None
            for candidate in ["easyocr", "paddleocr", "tesseract"]:
                try:
                    eng = selector.get_engine(candidate)
                    if eng.is_available():
                        working_engine = candidate
                        break
                except Exception:
                    pass

            if not working_engine:
                logger.info(
                    "OCR dependencies unavailable | job=%s | skipping OCR phase gracefully",
                    context.job_id,
                )
                context.ocr_result = None
                context.ocr_summary = {
                    "status": "UNAVAILABLE",
                    "reason": "OCR engine dependencies not installed in runtime environment",
                }
                msg = "OCR text extraction unavailable: Runtime dependencies not installed."
                context.add_warning(msg)
                warnings.append(msg)
                return StageResult.success(self.name, warnings=warnings)

            # Working engine exists
            service = OCRService(engine_name=working_engine)
            service.process(context)

            if context.ocr_result is None:
                warnings.append("OCR resulted in no output.")

            return StageResult.success(self.name, warnings=warnings)

        except Exception as e:
            msg = f"OCR engine processing failed: {str(e)}"
            logger.warning("OCR processing exception: %s", msg)
            context.add_warning(msg)
            warnings.append(msg)
            return StageResult.warning(self.name, warnings=warnings)

