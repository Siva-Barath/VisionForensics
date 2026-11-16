"""
Detector Health Monitor.
Tracks which detectors ran successfully, skipped, or failed.
"""
from typing import List, Dict
from app.pipeline.context import AnalysisContext
from .models import DetectorHealth

class DetectorHealthMonitor:
    def monitor(self, context: AnalysisContext) -> List[DetectorHealth]:
        health_list = []
        
        # In a real implementation, we would extract this from pipeline execution logs 
        # or context.metadata. For now we infer from evidence or context state.
        
        doc = context.structured_document
        
        # Logo Verification
        if not doc or not any(s.get("region_type") == "LOGO" for s in doc.get("sections", [])):
            health_list.append(DetectorHealth("Logo Verification", "SKIPPED", "No logo detected."))
        else:
            health_list.append(DetectorHealth("Logo Verification", "EXECUTED"))
            
        # Signature Verification
        if not doc or not any(s.get("region_type") == "SIGNATURE" for s in doc.get("sections", [])):
            health_list.append(DetectorHealth("Signature Verification", "SKIPPED", "No signature region detected."))
        else:
            health_list.append(DetectorHealth("Signature Verification", "EXECUTED"))
            
        return health_list
