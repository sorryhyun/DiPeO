"""IR data validators for different builder types."""

from .backend import BackendValidator
from .base import BaseValidator, CompositeValidator, ValidationError, ValidationResult
from .frontend import FrontendValidator
from .strawberry import StrawberryValidator

__all__ = [
    "BackendValidator",
    "BaseValidator",
    "CompositeValidator",
    "FrontendValidator",
    "StrawberryValidator",
    "ValidationError",
    "ValidationResult",
]


def get_validator(builder_type: str) -> BaseValidator:
    """Get validator for a specific builder type.

    Args:
        builder_type: Type of builder ('backend', 'frontend', 'strawberry')

    Returns:
        Appropriate validator instance

    Raises:
        ValueError: If builder type is unknown
    """
    validators = {
        "backend": BackendValidator,
        "frontend": FrontendValidator,
        "strawberry": StrawberryValidator,
    }

    validator_class = validators.get(builder_type)
    if not validator_class:
        available = ", ".join(validators.keys())
        raise ValueError(f"Unknown builder type: {builder_type}. Available: {available}")

    return validator_class()
