"""
Metadata Detector.

Analyzes document metadata for inconsistencies, suspicious software signatures,
or impossible timestamps.
"""

from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource

class MetadataDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "metadata_detector"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        evidence = []
        
        # We rely on Phase 2 MetadataStage to populate context.metadata
        meta = context.metadata or {}
        
        # Example rule: Missing metadata
        if not meta:
            # We don't necessarily flag completely missing metadata as high risk,
            # as some images strip it naturally.
            return evidence

        # Example rule: Suspicious software
        software = meta.get("software", "").lower()
        suspicious_keywords = ["photoshop", "gimp", "illustrator", "editor"]
        if any(kw in software for kw in suspicious_keywords):
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.METADATA,
                severity=70.0,
                description=f"Suspicious editing software detected in metadata: {software}",
                source=EvidenceSource.RULE_BASED,
                recommendation="Review the document for manual alterations."
            ))
            
        # Add more rules (e.g., modified date < created date, etc.) as needed.
        
        return evidence
