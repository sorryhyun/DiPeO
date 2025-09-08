"""Base provider class for integrated API providers."""

import logging
from abc import abstractmethod
from typing import Any

from dipeo.domain.base import ServiceError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.integrations.ports import ApiProvider as ApiProviderPort

logger = logging.getLogger(__name__)


class BaseApiProvider(LoggingMixin, InitializationMixin, ApiProviderPort):
    """Base class for API provider implementations."""

    def __init__(self, provider_name: str, supported_operations: list[str]):
        # Initialize mixins
        InitializationMixin.__init__(self)
        self._provider_name = provider_name
        self._supported_operations = supported_operations

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    @property
    def supported_operations(self) -> list[str]:
        """Get list of supported operations."""
        return self._supported_operations

    async def initialize(self) -> None:
        """Initialize the provider."""

    async def execute(
        self,
        operation: str,
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a specific operation."""
        if operation not in self.supported_operations:
            raise ValueError(
                f"Operation '{operation}' not supported by {self.provider_name}. "
                f"Supported operations: {', '.join(self.supported_operations)}"
            )

        if not api_key:
            raise ValueError(f"API key required for {self.provider_name} operations")

        try:
            return await self._execute_operation(
                operation=operation,
                config=config or {},
                resource_id=resource_id,
                api_key=api_key,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(f"{self.provider_name} operation '{operation}' failed: {e}")
            raise ServiceError(f"{self.provider_name} API error: {e!s}")

    @abstractmethod
    async def _execute_operation(
        self,
        operation: str,
        config: dict[str, Any],
        resource_id: str | None,
        api_key: str,
        timeout: float,
    ) -> dict[str, Any]:
        """Execute the actual operation. Must be implemented by subclasses."""
        ...

    async def validate_config(self, operation: str, config: dict[str, Any] | None = None) -> bool:
        """Validate operation configuration."""
        if operation not in self.supported_operations:
            return False

        # Default validation - can be overridden by subclasses
        return True

    def _build_error_response(self, error: Exception, operation: str) -> dict[str, Any]:
        """Build a standardized error response."""
        return {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "provider": self.provider_name,
                "operation": operation,
            },
        }

    def _build_success_response(self, data: Any, operation: str) -> dict[str, Any]:
        """Build a standardized success response."""
        return {
            "success": True,
            "data": data,
            "metadata": {"provider": self.provider_name, "operation": operation},
        }
