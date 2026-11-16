"""
Table Detector.

Modular framework to map grid-like geometric structures into StructuredTables.
Does not use CV yet; operates purely on OCR bounding box coordinates and density.
"""

from app.services.ocr.models import OCRPage
from app.services.layout.models import StructuredTable

class TableDetector:
    def detect(self, page: OCRPage) -> list[StructuredTable]:
        """
        Detects tables from OCR bounding box layouts.
        Currently a stub framework ready for geometric or CV-based grid logic.
        """
        tables = []
        # Future logic: Find aligned blocks/lines that form a grid
        # and populate StructuredTable(rows=[...])
        return tables
