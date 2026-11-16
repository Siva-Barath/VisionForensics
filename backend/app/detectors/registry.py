"""
DetectorRegistry — manages the set of active forensic detectors.

ForgeryStage calls `get_detectors()` and iterates — it never imports
a concrete detector class. This keeps the stage fully decoupled from
individual algorithm implementations.
"""

from __future__ import annotations

from typing import Optional

from app.detectors.base_detector import BaseDetector
from app.core.logging import get_logger

logger = get_logger(__name__)


class DetectorRegistry:
    def __init__(self) -> None:
        self._detectors: dict[str, BaseDetector] = {}

    def register(self, detector: BaseDetector) -> None:
        """Register a detector. Replaces any existing detector with the same name."""
        if detector.name in self._detectors:
            logger.warning("Detector '%s' is already registered — replacing", detector.name)
        self._detectors[detector.name] = detector
        logger.debug("Registered detector: %s v%s", detector.name, detector.version)

    def remove(self, name: str) -> None:
        """Remove a detector by name. No-op if not registered."""
        if name in self._detectors:
            del self._detectors[name]
            logger.debug("Removed detector: %s", name)

    def get_detectors(self, document_type: Optional[str] = None) -> list[BaseDetector]:
        """
        Return all detectors that support the given document type.
        If document_type is None, returns all registered detectors.
        """
        return [d for d in self._detectors.values() if d.supports(document_type)]

    def detector_names(self) -> list[str]:
        return list(self._detectors.keys())

    def __len__(self) -> int:
        return len(self._detectors)
