"""
Evidence Aggregator.

Collects evidence from every detector, removes duplicates, sorts by severity,
and generates EvidenceSummary statistics.
"""

from typing import List
from app.services.forensics.models import Evidence, EvidenceSummary

class EvidenceAggregator:
    def aggregate(self, evidence_list: List[Evidence]) -> tuple[List[Evidence], EvidenceSummary]:
        """
        Merge and summarize evidence.
        """
        # Remove exact duplicates if any
        seen = set()
        unique_evidence = []
        for ev in evidence_list:
            # simple hash for deduplication based on description and severity
            h = f"{ev.detector}_{ev.description}_{ev.severity}"
            if h not in seen:
                seen.add(h)
                unique_evidence.append(ev)
                
        # Sort by severity descending
        unique_evidence.sort(key=lambda x: x.severity, reverse=True)
        
        highest_sev = unique_evidence[0].severity if unique_evidence else 0.0
        
        category_counts = {}
        source_counts = {}
        
        for ev in unique_evidence:
            cat = ev.category.value
            src = ev.source.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            source_counts[src] = source_counts.get(src, 0) + 1
            
        summary = EvidenceSummary(
            total_evidence=len(unique_evidence),
            highest_severity=highest_sev,
            category_counts=category_counts,
            source_counts=source_counts
        )
        
        return unique_evidence, summary
