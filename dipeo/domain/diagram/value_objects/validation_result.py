"""Validation result value object."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge with another validation result."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings
        )