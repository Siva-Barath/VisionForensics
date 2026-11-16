"""
Decision Trace Builder.
"""
from app.services.evidence_fusion.models import FinalForensicAssessment

class DecisionTraceBuilder:
    def build(self, assessment: FinalForensicAssessment) -> str:
        trace_str = "Prior Risk: 5.0%\n\n"
        
        for step in assessment.decision_trace.steps:
            if step.stage == "Initialization": continue
            
            trace_str += "↓\n\n"
            trace_str += f"{step.stage}\n"
            trace_str += f"{step.value_change}\n\n"
            
        trace_str += "↓\n\n"
        trace_str += f"Posterior: {(assessment.calibrated_risk * 100):.1f}%\n\n"
        trace_str += "↓\n\n"
        trace_str += f"Verdict: {assessment.verdict.name}"
        
        return trace_str
