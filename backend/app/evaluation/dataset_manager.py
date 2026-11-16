"""
Dataset Manager.
"""
from typing import Dict, List

class DatasetManager:
    def load_splits(self, config_path: str) -> Dict[str, List[str]]:
        # Mock dataset manager
        return {
            "authentic": ["doc1.pdf", "doc2.pdf"],
            "forged": ["doc3.pdf", "doc4.pdf"]
        }
        
    def get_cross_document_categories(self) -> List[str]:
        return ["Passport", "Invoice", "Marksheet", "Signature Replacement", "Copy-Move"]
