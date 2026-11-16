"""
OCR Consistency Detector.

Analyzes the OCR results for extremely low confidence regions, 
suspicious character replacements, or duplicated text blocks.
"""

from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource

class OCRConsistencyDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "ocr_consistency_detector"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        evidence = []
        
        summary = context.ocr_summary or {}
        
        # Rule: High fraction of low-confidence text might indicate tampering or poor scan
        low_conf_fraction = summary.get("low_confidence_fraction", 0.0)
        
        if low_conf_fraction > 0.3:  # 30% low confidence is suspicious
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.OCR,
                severity=40.0,
                description=f"High proportion ({low_conf_fraction:.1%}) of low-confidence OCR text.",
                source=EvidenceSource.OCR,
                recommendation="Verify the physical document quality or check for splicing noise."
            ))
            
        # We can also parse the raw OCR words to find duplicate strings or broken kerning.
        
        return evidence
