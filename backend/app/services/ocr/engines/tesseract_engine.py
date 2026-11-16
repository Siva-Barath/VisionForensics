"""
Tesseract Engine implementation (Mocked).
"""

import numpy as np
import logging

from app.services.ocr.engines.base_engine import BaseEngine
from app.services.ocr.models import OCRPage

logger = logging.getLogger(__name__)


class TesseractEngine(BaseEngine):
    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        logger.info("Initializing Tesseract Engine (Mock)")
        self._initialized = True

    def is_available(self) -> bool:
        # This adapter has no real extraction implementation yet. An importable
        # dependency is not evidence that text examination can be executed.
        return False

    def extract_text(self, image: np.ndarray) -> str:
        raise RuntimeError("Tesseract extraction adapter is not implemented")

    def extract_words(self, image: np.ndarray) -> OCRPage:
        raise RuntimeError("OCR extraction adapter is not implemented")

    def extract_lines(self, image: np.ndarray) -> OCRPage:
        raise RuntimeError("OCR extraction adapter is not implemented")

    def extract_blocks(self, image: np.ndarray) -> OCRPage:
        raise RuntimeError("OCR extraction adapter is not implemented")
