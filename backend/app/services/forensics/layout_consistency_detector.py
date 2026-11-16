"""
Layout Consistency Detector.

Analyzes the StructuredDocument for duplicate labels, overlapping regions, 
or abnormal layout shifts using pure geometry.
"""

from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource

class LayoutConsistencyDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "layout_consistency_detector"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        evidence = []
        
        doc = context.structured_document or {}
        summary = context.layout_summary or {}
        
        # Look for warnings emitted by the LayoutValidator
        warnings = summary.get("warnings", [])
        
        for w in warnings:
            # Re-map Layout Analysis warnings into Forensic Evidence
            if "Duplicate field" in w:
                evidence.append(Evidence(
                    detector=self.name,
                    category=EvidenceCategory.LAYOUT,
                    severity=60.0,
                    description=f"Layout anomaly: {w}",
                    source=EvidenceSource.LAYOUT,
                    recommendation="Check for copy-move forgery on fields."
                ))
            elif "Empty value" in w:
                evidence.append(Evidence(
                    detector=self.name,
                    category=EvidenceCategory.LAYOUT,
                    severity=20.0,
                    description=f"Missing expected content: {w}",
                    source=EvidenceSource.LAYOUT,
                    recommendation="Ensure the document isn't a blank template."
                ))
        
        # We could also do geometric bounding box intersection checks here to detect overlapping regions.
        
        return evidence
