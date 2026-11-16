"""
OperationRegistry — manages the set of available preprocessing operations.

DecisionEngine requests operations by name from this registry.
It never instantiates operation classes directly, keeping it fully
decoupled from individual algorithm implementations.

To register a new operation, add it to the _build_default_registry()
call at the bottom of this module. No other file needs to change.
"""

from __future__ import annotations

from app.services.preprocessing.operations.base_operation import BaseOperation
from app.core.logging import get_logger

logger = get_logger(__name__)


class OperationRegistry:
    def __init__(self) -> None:
        self._operations: dict[str, BaseOperation] = {}

    def register(self, operation: BaseOperation) -> None:
        """Register an operation. Replaces any existing operation with the same name."""
        if operation.name in self._operations:
            logger.warning("Operation '%s' already registered — replacing", operation.name)
        self._operations[operation.name] = operation
        logger.debug("Registered preprocessing operation: %s v%s", operation.name, operation.version)

    def get(self, name: str) -> BaseOperation | None:
        """Return the operation registered under `name`, or None."""
        return self._operations.get(name)

    def get_all(self) -> list[BaseOperation]:
        """Return all registered operations in insertion order."""
        return list(self._operations.values())

    def names(self) -> list[str]:
        return list(self._operations.keys())

    def __len__(self) -> int:
        return len(self._operations)
