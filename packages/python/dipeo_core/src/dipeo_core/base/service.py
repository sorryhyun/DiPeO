"""Base service class for DiPeO services."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ValidationError


class BaseService(ABC):
    """Base service class with common functionality for DiPeO services."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the service with optional configuration.

        Args:
            config: Optional configuration dictionary for the service
        """
        self.config = config or {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Must be implemented by subclasses."""
        pass

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: list[str]
    ) -> None:
        """Validate that all required fields are present in the data.

        Args:
            data: Dictionary to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def validate_file_path(
        self, file_path: str, allowed_base: Optional[Path] = None
    ) -> Path:
        """Validate file path for security.

        Args:
            file_path: Path to validate
            allowed_base: Optional base path for security restrictions

        Returns:
            Resolved Path object

        Raises:
            ValidationError: If the path is outside allowed base
        """
        rel_path = Path(file_path)
        
        # If no base path restriction, just resolve the path
        if allowed_base is None:
            return rel_path.resolve()
            
        full_path = (allowed_base / rel_path).resolve()

        # Check if the resolved path is within the allowed base
        try:
            full_path.relative_to(allowed_base)
        except ValueError:
            raise ValidationError(f"Access to {full_path} is forbidden")

        return full_path

    def safe_get_nested(self, obj: Any, path: str, default: Any = None) -> Any:
        """Safely get nested value from object using dot notation.

        Args:
            obj: Object to traverse
            path: Dot-separated path (e.g., "user.profile.name")
            default: Default value if path not found

        Returns:
            Value at path or default
        """
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
        """Get configuration value with optional default.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.safe_get_nested(self.config, key, default)