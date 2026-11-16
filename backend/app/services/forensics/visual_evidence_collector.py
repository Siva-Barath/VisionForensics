"""
Visual Evidence Collector.

Gathers suspicious bounding boxes from all gathered evidence so they can
be highlighted visually in the final report.
"""

from typing import List
from app.services.forensics.models import Evidence, EvidenceRegion

class VisualEvidenceCollector:
    def collect(self, evidence_list: List[Evidence]) -> List[dict]:
        """
        Extracts all regions from evidence list for visualization.
        """
        visuals = []
        
        for ev in evidence_list:
            for idx, region in enumerate(ev.regions):
                region_id = f"{getattr(ev, 'id', 'reg')}_{idx}"
                page_idx = getattr(region, "page_index", None)
                if page_idx is None:
                    page_idx = getattr(ev, "page_index", 0)
                if page_idx is None:
                    page_idx = 0

                visuals.append({
                    "id": region_id,
                    "evidence_id": getattr(ev, "id", None),
                    "detector": ev.detector,
                    "category": ev.category.value,
                    "severity": float(ev.severity),
                    "confidence": float(getattr(ev, "confidence", 1.0)),
                    "description": region.description or ev.description,
                    "page_index": int(page_idx),
                    "bounding_box": {
                        "points": region.bounding_box.points
                    }
                })
                
        return visuals
