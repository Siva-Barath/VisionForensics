"""
Document Classification Stage — Phase 8.

Runs immediately after Layout Analysis and Forgery Detection to classify the 
document type before specific field extraction or downstream reporting.
"""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.classification import ClassificationService, DocumentProfileRegistry
from dataclasses import asdict

class DocumentClassificationStage(BaseStage):
    name = "document_classification"

    async def run(self, context: AnalysisContext) -> StageResult:
        registry = DocumentProfileRegistry()
        service = ClassificationService(registry)
        
        result = service.process(context)
        
        # Update context
        context.document_type = result.predicted_type.value
        context.classification_result = asdict(result)
        
        # For legacy compatibility or future ML use
        context.document_profile = {
            "type": result.predicted_type.value,
            "confidence": result.confidence
        }
        
        warnings = []
        if result.predicted_type.value == "UNKNOWN":
            if context.ocr_result is None:
                warnings.append("Document classification unassigned: OCR text extraction was unavailable.")
            else:
                warnings.append("Document type unclassified: Document content did not match standard profiles.")
            
        return StageResult.success(self.name, warnings=warnings)
