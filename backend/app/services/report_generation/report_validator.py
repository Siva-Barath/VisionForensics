"""
Report Validator.
"""
from .models import GeneratedReport, ReportValidationResult

class ReportValidator:
    def validate(self, report: GeneratedReport) -> ReportValidationResult:
        errors = []
        warnings = []
        
        if not report.document_name:
            errors.append("Executive Summary missing document name.")
        if not report.final_verdict:
            errors.append("Verdict missing.")
        if not report.decision_trace_rendered:
            errors.append("Decision Trace missing.")
            
        if not report.evidence_table:
            warnings.append("Evidence Table is empty (No forensic anomalies found).")
            
        if not report.recommendations:
            warnings.append("No recommendations present.")
            
        is_valid = len(errors) == 0
        return ReportValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
