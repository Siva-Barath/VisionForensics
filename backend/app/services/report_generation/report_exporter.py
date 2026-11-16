"""
Report Exporter (Mock HTML/JSON).
"""
import json
from dataclasses import asdict
from .models import GeneratedReport
from .config import ReportGenerationConfig

class ReportExporter:
    def export_json(self, report: GeneratedReport) -> str:
        return json.dumps(asdict(report), indent=2)
        
    def export_csv(self, report: GeneratedReport) -> str:
        csv = "Detector,Severity,Confidence,Reliability,RiskContribution,Status\n"
        for row in report.evidence_table:
            csv += f"{row.detector},{row.severity},{row.confidence},{row.reliability},{row.risk_contribution},{row.status}\n"
        return csv
        
    def export_html(self, report: GeneratedReport, config: ReportGenerationConfig) -> str:
        # Mock HTML template
        return f"<html><body><h1>{config.watermark_text}</h1><h2>{report.document_name} - {report.final_verdict}</h2></body></html>"
