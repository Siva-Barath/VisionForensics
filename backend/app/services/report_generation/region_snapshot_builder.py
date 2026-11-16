"""
Region Snapshot Builder.
"""
from typing import List
from app.services.forensics.models import Evidence
from .models import RegionSnapshot

class RegionSnapshotBuilder:
    def build(self, raw_evidence: List[Evidence]) -> List[RegionSnapshot]:
        snapshots = []
        for e in raw_evidence:
            if e.regions:
                for r in e.regions:
                    # In a real impl, this would trigger an image crop based on r.points
                    snapshot = RegionSnapshot(
                        region_id=r.region_id,
                        detector=e.detector,
                        severity=e.severity,
                        confidence=e.confidence,
                        explanation=e.description,
                        crop_path=f"assets/regions/{r.region_id}.jpg",
                        overlay_path=f"assets/overlays/{r.region_id}.jpg"
                    )
                    snapshots.append(snapshot)
        return snapshots
