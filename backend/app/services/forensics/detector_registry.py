"""
Detector Registry.

Manages all available forgery detectors, allowing them to be dynamically
plugged into the ForgeryService without modifying core business logic.
"""

import logging
from typing import Dict, List
from app.services.forensics.base_detector import BaseDetector

logger = logging.getLogger(__name__)

class DetectorRegistry:
    def __init__(self):
        self._detectors: Dict[str, BaseDetector] = {}

    def register(self, detector: BaseDetector) -> None:
        """Register a new detector."""
        if detector.name in self._detectors:
            logger.warning("Overwriting existing detector '%s' in registry.", detector.name)
        self._detectors[detector.name] = detector
        logger.debug("Registered forgery detector: %s", detector.name)

    def unregister(self, detector_name: str) -> None:
        """Remove a detector from the registry."""
        if detector_name in self._detectors:
            del self._detectors[detector_name]

    def get_all(self) -> List[BaseDetector]:
        """Return all registered detectors."""
        return list(self._detectors.values())
