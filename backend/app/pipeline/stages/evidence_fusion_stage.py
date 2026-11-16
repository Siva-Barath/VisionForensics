"""
Evidence Fusion Stage.
"""
from typing import Optional
import logging

from app.pipeline.context import AnalysisContext
from app.pipeline.base_stage import BaseStage
from app.services.evidence_fusion import EvidenceFusionService

logger = logging.getLogger(__name__)

class EvidenceFusionStage(BaseStage):
    def __init__(self, service: Optional[EvidenceFusionService] = None):
        super().__init__("Evidence Fusion")
        self.service = service or EvidenceFusionService()

    def process(self, context: AnalysisContext):
        if not context.evidence:
            logger.info("No evidence to fuse.")
            # We can still run fusion to get a baseline authentic verdict and health
            
        final_assessment = self.service.fuse(context.evidence, context)
        context.final_assessment = final_assessment
        
        logger.info(f"Fusion complete. Verdict: {final_assessment.verdict.name}, Calibrated Risk: {final_assessment.calibrated_risk:.2%}")
