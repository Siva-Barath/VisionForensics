"""
Engine Selector for OCR.

Uses a registry pattern to decouple OCR backends from the processing pipeline.
Allows switching engines seamlessly or falling back to alternatives.
"""

import logging
from typing import Dict, Type

from app.services.ocr.engines import (
    BaseEngine,
    EasyOCREngine,
    TesseractEngine,
    PaddleOCREngine
)

logger = logging.getLogger(__name__)


class EngineSelector:
    def __init__(self):
        self._registry: Dict[str, Type[BaseEngine]] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("easyocr", EasyOCREngine)
        self.register("tesseract", TesseractEngine)
        self.register("paddleocr", PaddleOCREngine)

    def register(self, name: str, engine_class: Type[BaseEngine]) -> None:
        """Register a new engine class."""
        self._registry[name.lower()] = engine_class
        logger.debug("Registered OCR engine: %s", name.lower())

    def get_engine(self, name: str) -> BaseEngine:
        """Instantiate and return the requested engine if available."""
        name = name.lower()
        if name not in self._registry:
            raise ValueError(f"OCR engine '{name}' is not registered.")
        
        engine_class = self._registry[name]
        engine = engine_class()
        
        if not engine.is_available():
            raise RuntimeError(f"OCR engine '{name}' is registered but its dependencies are not available.")
            
        return engine

    def get_available_engines(self) -> list[str]:
        return list(self._registry.keys())
