"""
DecisionEngine — selects which preprocessing operations to run based on QualityMetrics.

Rules are simple threshold comparisons for now.
The engine requests operations from OperationRegistry — it never instantiates them directly.
"""

from __future__ import annotations

from app.services.preprocessing.models import QualityMetrics
from app.services.preprocessing.operations.registry import OperationRegistry
from app.services.preprocessing.operations.base_operation import BaseOperation
from app.core.logging import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Thresholds — adjust here without touching any operation code        #
# ------------------------------------------------------------------ #
_BLUR_THRESHOLD = 100.0       # Laplacian variance below this → denoise
_CONTRAST_THRESHOLD = 40.0    # Std-dev below this → contrast enhancement
_BRIGHTNESS_LOW = 50.0        # Mean brightness below this → contrast enhancement
_BRIGHTNESS_HIGH = 210.0      # Mean brightness above this → normalization
_SKEW_THRESHOLD = 0.5         # Absolute skew angle above this → deskew (Phase 3)


class DecisionEngine:
    """
    Selects preprocessing operations for a page based on its QualityMetrics.

    Args:
        registry: OperationRegistry to resolve operation instances from.
    """

    def __init__(self, registry: OperationRegistry) -> None:
        self._registry = registry

    def select(self, metrics: QualityMetrics) -> list[BaseOperation]:
        """
        Return an ordered list of operations to apply to this page.

        Operations are returned in the recommended execution order:
        geometry corrections first, then photometric corrections.
        """
        selected_names: list[str] = []

        # --- Geometry ---
        # Skew correction (placeholder — skew_angle is None until Phase 3)
        if metrics.skew_angle is not None and abs(metrics.skew_angle) > _SKEW_THRESHOLD:
            selected_names.append("deskew")

        # Perspective correction is not auto-selected by metrics alone;
        # it will be triggered by document-type rules in Phase 3.

        # --- Photometric ---
        if metrics.blur_score < _BLUR_THRESHOLD:
            selected_names.append("denoise")

        if metrics.contrast < _CONTRAST_THRESHOLD or metrics.brightness < _BRIGHTNESS_LOW:
            selected_names.append("contrast")

        if metrics.brightness > _BRIGHTNESS_HIGH:
            selected_names.append("normalize")

        # Always normalize as the final step when any other operation ran
        if selected_names and "normalize" not in selected_names:
            selected_names.append("normalize")

        # Resolve names → operation instances (skip any not in registry)
        operations: list[BaseOperation] = []
        for name in selected_names:
            op = self._registry.get(name)
            if op is None:
                logger.warning("DecisionEngine selected '%s' but it is not registered", name)
                continue
            if not op.enabled:
                logger.debug("Skipping disabled operation: %s", name)
                continue
            operations.append(op)

        logger.debug(
            "DecisionEngine selected %d operation(s): %s",
            len(operations),
            [op.name for op in operations],
        )
        return operations
