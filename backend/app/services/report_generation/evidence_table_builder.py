"""
Evidence Table Builder.
"""
from typing import List, Tuple
from app.services.evidence_fusion.models import FinalForensicAssessment
from app.services.forensics.models import Evidence
from .models import EvidenceSummaryEntry, TraceabilityEntry

class EvidenceTableBuilder:
    def build(self, assessment: FinalForensicAssessment, raw_evidence: List[Evidence]) -> Tuple[List[EvidenceSummaryEntry], List[TraceabilityEntry]]:
        table = []
        traceability = []
        
        # We need to correlate EvidenceContribution to raw Evidence
        for contrib in sorted(assessment.breakdown.contributors, key=lambda c: c.risk_shift, reverse=True):
            # Find matching raw evidence
            matching = [e for e in raw_evidence if e.category.name == contrib.category]
            
            for m in matching:
                entry = EvidenceSummaryEntry(
                    detector=m.detector,
                    severity=m.severity,
                    confidence=m.confidence,
                    reliability=m.reliability,
                    risk_contribution=contrib.risk_shift,
                    status="Suspicious" if m.severity > 50 else "Authentic"
                )
                table.append(entry)
                
                # Traceability
                region_id = m.regions[0].region_id if m.regions else "Global"
                rec = m.recommendation or "No specific recommendation"
                trace = TraceabilityEntry(
                    evidence_description=m.description,
                    detector=m.detector,
                    region_id=region_id,
                    recommendation=rec
                )
                traceability.append(trace)
                
        return table, traceability
