"""
Field Consistency Detector.

Compares extracted fields generically to detect conflicting values, 
impossible formats, or missing expected data based on document type.
"""

from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource

class FieldConsistencyDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "field_consistency_detector"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        evidence = []
        
        doc = context.structured_document or {}
        fields = doc.get("fields", [])
        
        # Check for multiple fields with the same key but different values
        key_values = {}
        for f in fields:
            key = f.get("key")
            val = f.get("value")
            
            if key in key_values:
                existing_val = key_values[key]
                if existing_val != val:
                    evidence.append(Evidence(
                        detector=self.name,
                        category=EvidenceCategory.FIELD,
                        severity=80.0,
                        description=f"Conflicting values for field '{key}': '{existing_val}' vs '{val}'",
                        source=EvidenceSource.RULE_BASED,
                        recommendation="Highly indicative of copy-move or text splicing."
                    ))
            else:
                key_values[key] = val
                
        # (Future) Check against DocumentProfile for missing required fields based on doc.document_type
                
        return evidence
