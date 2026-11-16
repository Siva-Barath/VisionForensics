"""
Executive Summary Builder.
"""
from app.services.evidence_fusion.models import FinalForensicAssessment
from .models import GeneratedReport
from .config import ReportGenerationConfig

class ExecutiveSummaryBuilder:
    def build(self, assessment: FinalForensicAssessment, config: ReportGenerationConfig) -> GeneratedReport:
        # A simple heuristic for Explainability Score
        exp_score = min(100, len(assessment.breakdown.contributors) * 15 + (assessment.overall_confidence or 0) * 50)
        
        report = GeneratedReport(
            document_name=assessment.document_name or "Unknown Document",
            document_type=assessment.document_type or "Unknown Type",
            overall_forgery_risk=assessment.calibrated_risk,
            final_verdict=assessment.verdict.name,
            confidence=assessment.overall_confidence or 0.0,
            explainability_score=exp_score,
            sensitivity_profile=assessment.sensitivity_profile or config.profile.name,
            processing_time_ms=assessment.execution_time_ms or 0.0
        )
        return report
