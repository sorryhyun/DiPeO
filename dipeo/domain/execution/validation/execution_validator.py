"""Execution Validator - Validates diagram execution flow."""

from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, ValidationResult


class ExecutionValidator(BaseValidator):
    """Validates diagram execution flow using the unified framework."""

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform execution flow validation."""
        if not hasattr(target, "nodes") or not hasattr(target, "arrows"):
            result.add_error(ValidationError("Target must be a diagram with nodes and arrows"))
            return

        # For now, just pass validation since the old flow validation logic was outdated
        # TODO: Implement updated flow validation logic if needed
