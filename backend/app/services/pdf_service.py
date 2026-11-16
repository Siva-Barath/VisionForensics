"""
PDFService — converts PDF documents to per-page PNG images.

Wraps the low-level pdf_converter utility and resolves output paths
via StorageService so no other layer needs to know where files live.
"""

from __future__ import annotations

from pathlib import Path

from app.services.storage_service import StorageService
from app.services.preprocessing.pdf_converter import convert_pdf_to_images
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFService:
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def convert(self, pdf_path: Path, document_id: str) -> list[str]:
        """
        Convert a PDF to page images.

        Args:
            pdf_path: Absolute path to the stored PDF file.
            document_id: Used to namespace output filenames.

        Returns:
            Ordered list of paths to the generated page PNG files.
        """
        output_dir = self._storage.processed_dir(document_id)
        logger.debug("Converting PDF | document=%s output_dir=%s", document_id, output_dir)
        return convert_pdf_to_images(pdf_path, output_dir, document_id)
