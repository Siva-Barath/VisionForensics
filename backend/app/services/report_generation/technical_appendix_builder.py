"""
Technical Appendix Builder.
"""
import hashlib
import json
from typing import List, Dict, Any
from datetime import datetime
from app.services.evidence_fusion.models import FinalForensicAssessment
from .models import TechnicalAppendix, ReportIntegrity, ChainOfCustodyEntry, TraceabilityEntry
from .config import ReportGenerationConfig

class TechnicalAppendixBuilder:
    def build(self, 
              assessment: FinalForensicAssessment, 
              config: ReportGenerationConfig, 
              traceability: List[TraceabilityEntry],
              evidence_json_str: str) -> TechnicalAppendix:
              
        integrity = ReportIntegrity(
            software_version=config.software_version,
            evidence_hash_sha256=hashlib.sha256(evidence_json_str.encode()).hexdigest(),
            # assets_hash and report_hash would be calculated at final assembly
        )
        
        now = datetime.utcnow().isoformat()
        chain = [
            ChainOfCustodyEntry(now, "Document Uploaded", "SYSTEM"),
            ChainOfCustodyEntry(now, "Analysis Started", "SYSTEM"),
            ChainOfCustodyEntry(now, "Evidence Fusion Completed", "SYSTEM"),
            ChainOfCustodyEntry(now, "Report Generated", "SYSTEM")
        ]
        
        health_dicts = [{"detector": h.detector_name, "status": h.status, "reason": h.reason or "N/A"} for h in assessment.detector_health]
        
        config_dump = {
            "sensitivity_profile": assessment.sensitivity_profile,
            "software_version": config.software_version,
            "report_version": config.report_version
        }
        
        return TechnicalAppendix(
            integrity=integrity,
            chain_of_custody=chain,
            traceability_matrix=traceability,
            configuration_dump=config_dump,
            detector_health=health_dicts
        )
