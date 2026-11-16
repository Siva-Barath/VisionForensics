"""
Archive Builder.
"""
from typing import Dict

class ArchiveBuilder:
    def build_archive(self, json_data: str, csv_data: str, html_data: str, assets: Dict[str, str]) -> bytes:
        # Mock ZIP compilation
        # In reality, would use zipfile.ZipFile in memory
        return b"MOCK_ZIP_ARCHIVE_DATA"
