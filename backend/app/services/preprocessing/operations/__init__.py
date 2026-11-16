from app.services.preprocessing.operations.base_operation import BaseOperation
from app.services.preprocessing.operations.registry import OperationRegistry
from app.services.preprocessing.operations.deskew import DeskewOperation
from app.services.preprocessing.operations.perspective import PerspectiveCorrectionOperation
from app.services.preprocessing.operations.denoise import DenoiseOperation
from app.services.preprocessing.operations.contrast import ContrastEnhancementOperation
from app.services.preprocessing.operations.shadow import ShadowRemovalOperation
from app.services.preprocessing.operations.normalize import NormalizationOperation


def build_default_registry() -> OperationRegistry:
    """Construct and return an OperationRegistry pre-loaded with all operations."""
    registry = OperationRegistry()
    registry.register(DeskewOperation())
    registry.register(PerspectiveCorrectionOperation())
    registry.register(DenoiseOperation())
    registry.register(ContrastEnhancementOperation())
    registry.register(ShadowRemovalOperation())
    registry.register(NormalizationOperation())
    return registry


__all__ = [
    "BaseOperation",
    "OperationRegistry",
    "build_default_registry",
    "DeskewOperation",
    "PerspectiveCorrectionOperation",
    "DenoiseOperation",
    "ContrastEnhancementOperation",
    "ShadowRemovalOperation",
    "NormalizationOperation",
]
