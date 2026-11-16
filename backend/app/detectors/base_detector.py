"""
BaseDetector — abstract interface for all forensic analysis detectors.

A Detector is a self-contained algorithm that analyses page images and
returns a structured finding. Detectors are registered with DetectorRegistry
and invoked by ForgeryStage (Phase 3) — the stage itself never imports a
concrete detector class.

Implementing a new detector:
  1. Create app/detectors/my_detector.py
  2. Subclass BaseDetector, set `name` and `supported_document_types`
  3. Implement `run(page_images, context)`
  4. Register with DetectorRegistry in app/__init__.py

Nothing else needs to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.logging import get_logger


class BaseDetector(ABC):
    """Abstract base class for all forensic detectors."""

    #: Unique detector identifier, e.g. "copy_move", "splicing", "ela"
    name: str = ""

    #: Human-readable description shown in reports and debug output
    description: str = ""

    #: Semantic version of this detector implementation
    version: str = "0.1.0"

    #: Document types this detector is designed for.
    #: Empty list means the detector runs on all document types.
    supported_document_types: list[str] = []

    def __init__(self) -> None:
        if not self.name:
            raise TypeError(f"{self.__class__.__name__} must define a non-empty `name` attribute")
        self._logger = get_logger(f"detector.{self.name}")

    @abstractmethod
    async def run(
        self,
        page_images: list[str],
        context_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyse the provided page images and return a findings dictionary.

        Args:
            page_images: Ordered list of paths to page PNG images.
            context_metadata: Lightweight dict of context fields the detector
                              may need (document_type, file_type, etc.).
                              Pass only what is needed — detectors must not
                              receive the full AnalysisContext to stay decoupled.

        Returns:
            A dict containing detector-specific findings. The structure is
            defined by each detector and consumed by the Risk Engine.
        """

    def confidence(self, findings: dict[str, Any]) -> Optional[float]:
        """
        Derive a 0.0–1.0 confidence score from the findings dict.

        Override in subclasses that produce a meaningful score.
        Returns None by default (no score available).
        """
        return None

    def supports(self, document_type: Optional[str]) -> bool:
        """Return True if this detector should run for the given document type."""
        if not self.supported_document_types:
            return True  # runs on all types
        return document_type in self.supported_document_types
