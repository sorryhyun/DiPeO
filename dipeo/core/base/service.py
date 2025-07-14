"""Base service class for DiPeO services."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .exceptions import ValidationError


class BaseService(ABC):
    """Base service class with common functionality for DiPeO services."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    async def initialize(self) -> None:
        pass

    def validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> None:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def validate_file_path(
        self, file_path: str, allowed_base: Path | None = None
    ) -> Path:
        # Validate file path for security
        rel_path = Path(file_path)

        if allowed_base is None:
            return rel_path.resolve()

        full_path = (allowed_base / rel_path).resolve()
        try:
            full_path.relative_to(allowed_base)
        except ValueError:
            raise ValidationError(f"Access to {full_path} is forbidden")

        return full_path

    def safe_get_nested(self, obj: Any, path: str, default: Any = None) -> Any:
        # Get nested value using dot notation
        if obj is None:
            return default

        current = obj
        parts = path.split(".")

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part, default)
                else:
                    current = getattr(current, part, default)

                if current is None:
                    return default

            return current
        except (KeyError, AttributeError, TypeError):
            return default

    def get_config_value(self, key: str, default: Any = None) -> Any:
        return self.safe_get_nested(self.config, key, default)
