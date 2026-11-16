"""
Forgery Detection Stage — Phase 5.
Coordinates evidence gathering across the Forgery Detection Framework.
"""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.forensics import (
    ForgeryService, 
    DetectorRegistry,
    MetadataDetector,
    ImageArtifactDetector,
    OCRConsistencyDetector,
    LayoutConsistencyDetector,
    FieldConsistencyDetector,
    SignatureRegionAnalyzer,
    LogoRegionAnalyzer,
    CopyMoveRegionAnalyzer
)

class ForgeryDetectionStage(BaseStage):
    name = "forgery"

    async def run(self, context: AnalysisContext) -> StageResult:
        registry = DetectorRegistry()
        
        # Register all decoupled detectors
        registry.register(MetadataDetector())
        registry.register(ImageArtifactDetector())
        registry.register(OCRConsistencyDetector())
        registry.register(LayoutConsistencyDetector())
        registry.register(FieldConsistencyDetector())
        registry.register(SignatureRegionAnalyzer())
        registry.register(LogoRegionAnalyzer())
        registry.register(CopyMoveRegionAnalyzer())
        
        service = ForgeryService(registry)
        service.process(context)
        
        warnings = []
        if context.forgery_report is None:
            warnings.append("Forgery detection failed to produce a report.")
            
        return StageResult.success(self.name, warnings=warnings)
