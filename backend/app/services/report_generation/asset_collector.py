"""
Asset Collector.
"""
from typing import Dict

class AssetCollector:
    def collect(self, document_id: str) -> Dict[str, str]:
        # Mock asset collection mapping internal temp paths to export paths
        return {
            "original": f"assets/original/{document_id}.pdf",
            "annotated": f"assets/annotated/{document_id}.pdf",
            "dashboard_snapshot": "assets/overlays/dashboard.png"
        }
