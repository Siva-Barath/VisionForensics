"""
BaseOperation — abstract base class for every image preprocessing operation.

To add a new preprocessing algorithm:
  1. Create a subclass in app/services/preprocessing/operations/
  2. Set `name`, `description`, and optionally `version`
  3. Implement `execute(image, context)` — return the (possibly modified) image
  4. Optionally override `validate(image)` for pre-condition checks
  5. Register the instance with OperationRegistry in operations/__init__.py

Nothing else in the codebase needs to change.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


class BaseOperation(ABC):
    """Abstract base class for all image preprocessing operations."""

    #: Unique operation identifier, e.g. "deskew", "denoise"
    name: str = ""

    #: Human-readable description
    description: str = ""

    #: Semantic version of this operation implementation
    version: str = "0.1.0"

    #: When False the DecisionEngine skips this operation even if selected
    enabled: bool = True

    def __init__(self) -> None:
        if not self.name:
            raise TypeError(
                f"{self.__class__.__name__} must define a non-empty `name` attribute"
            )
        self._logger = get_logger(f"preprocessing.operation.{self.name}")

    # ------------------------------------------------------------------ #
    # Contract                                                             #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def execute(
        self,
        image: np.ndarray,
        context: "AnalysisContext",
        **kwargs: Any,
    ) -> np.ndarray:
        """
        Apply this operation to the image and return the result.

        Must return the image unchanged until the algorithm is implemented.
        Raise StageError for recoverable failures.
        """

    def validate(self, image: np.ndarray) -> list[str]:
        """
        Check pre-conditions before executing.

        Returns a list of warning strings; empty list means the image is valid.
        Override in subclasses to add operation-specific checks.
        """
        if image is None or image.size == 0:
            return [f"{self.name}: received empty image"]
        return []

    # ------------------------------------------------------------------ #
    # Execution wrapper — called by PreprocessingService                  #
    # ------------------------------------------------------------------ #

    def run(
        self,
        image: np.ndarray,
        context: "AnalysisContext",
        **kwargs: Any,
    ) -> tuple[np.ndarray, list[str]]:
        """
        Wraps execute() with validation, timing, and structured logging.
        PreprocessingService calls this — never execute() directly.

        Returns:
            (processed_image, warnings)
        """
        if not self.enabled:
            self._logger.info(
                "Operation skipped (disabled) | op=%s | job=%s",
                self.name, context.job_id,
            )
            return image, [f"{self.name}: operation is disabled"]

        warnings = self.validate(image)
        if warnings:
            self._logger.warning(
                "Operation skipped (validation failed) | op=%s | job=%s | %s",
                self.name, context.job_id, warnings,
            )
            return image, warnings

        self._logger.info(
            "Operation started | op=%s v%s | job=%s",
            self.name, self.version, context.job_id,
        )
        start = time.perf_counter()
        warning_count = len(context.warnings)
        result = self.execute(image, context, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._logger.info(
            "Operation completed | op=%s | job=%s | duration=%.1fms",
            self.name, context.job_id, elapsed_ms,
        )
        return result, context.warnings[warning_count:]

    def metadata(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
        }
