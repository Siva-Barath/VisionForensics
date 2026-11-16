"""
Abstract Base Engine for OCR.

Every OCR engine must inherit from this interface.
Ensures uniform execution regardless of backend library.
"""

from abc import ABC, abstractmethod
import numpy as np

from app.services.ocr.models import OCRPage


class BaseEngine(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the OCR engine and load weights."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the underlying OCR library is installed and available."""
        pass

    @abstractmethod
    def extract_text(self, image: np.ndarray) -> str:
        """Extract plain text from the image."""
        pass

    @abstractmethod
    def extract_words(self, image: np.ndarray) -> OCRPage:
        """Extract words with bounding boxes and confidences."""
        pass

    @abstractmethod
    def extract_lines(self, image: np.ndarray) -> OCRPage:
        """Extract lines of text."""
        pass

    @abstractmethod
    def extract_blocks(self, image: np.ndarray) -> OCRPage:
        """Extract distinct blocks of text."""
        pass

    def extract_batch(self, images: list[np.ndarray]) -> list[OCRPage]:
        """
        Extract text from a batch of images.
        Default implementation loops over single images. Engines can override
        this to leverage batch inference.
        """
        return [self.extract_words(img) for img in images]
