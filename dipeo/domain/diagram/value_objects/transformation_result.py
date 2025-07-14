"""Transformation result value object."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TransformationResult:
    """Immutable result of a transformation."""
    transformed_value: Any
    original_value: Any
    transformation_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def changed(self) -> bool:
        """Check if value was changed."""
        return self.transformed_value != self.original_value