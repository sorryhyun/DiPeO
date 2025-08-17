"""Integrated API Service port interface.

DEPRECATED: This module re-exports domain types for backward compatibility.
Use dipeo.domain.integrations directly for new code.
"""

import warnings
from typing import Any, Optional, Protocol, runtime_checkable

# Re-export domain types
from dipeo.domain.integrations import ApiInvoker, ApiProvider, ApiProviderRegistry

warnings.warn(
    "dipeo.core.ports.integrated_api_service is deprecated. "
    "Use dipeo.domain.integrations instead.",
    DeprecationWarning,
    stacklevel=2,
)


@runtime_checkable
class IntegratedApiServicePort(Protocol):
    """Legacy integrated API service port - wraps new domain ApiInvoker for backward compatibility."""

    async def register_provider(self, provider_name: str, provider_instance: Any) -> None:
        """Register a new API provider.
        
        Args:
            provider_name: The name of the provider (e.g., 'notion', 'slack')
            provider_instance: The provider implementation instance
        """
        ...

    async def execute_operation(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> dict[str, Any]:
        """Execute an operation on a specific provider.
        
        Args:
            provider: The API provider to use
            operation: The operation to perform (provider-specific)
            config: Provider-specific configuration
            resource_id: Optional resource identifier
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            
        Returns:
            Operation result as a dictionary
            
        Raises:
            ValueError: If provider or operation is not supported
            ServiceError: On execution failures
        """
        ...

    def get_supported_providers(self) -> list[str]:
        """Get list of currently registered providers.
        
        Returns:
            List of provider names
        """
        ...

    def get_provider_operations(self, provider: str) -> list[str]:
        """Get supported operations for a specific provider.
        
        Args:
            provider: The provider name
            
        Returns:
            List of operation names
            
        Raises:
            ValueError: If provider is not registered
        """
        ...

    async def validate_operation(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Validate if an operation is supported and properly configured.
        
        Args:
            provider: The provider name
            operation: The operation name
            config: Operation configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...


@runtime_checkable
class ApiProviderPort(Protocol):
    """Legacy API provider port - wraps new domain ApiProvider for backward compatibility."""

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        ...

    @property
    def supported_operations(self) -> list[str]:
        """Get list of supported operations."""
        ...

    async def execute(
        self,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute a specific operation.
        
        Args:
            operation: The operation to perform
            config: Operation-specific configuration
            resource_id: Optional resource identifier
            api_key: API key for authentication
            timeout: Request timeout
            
        Returns:
            Operation result
            
        Raises:
            ValueError: If operation is not supported
            ServiceError: On execution failures
        """
        ...

    async def validate_config(
        self,
        operation: str,
        config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Validate operation configuration.
        
        Args:
            operation: The operation name
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...


# Export domain types for backward compatibility
__all__ = [
    "IntegratedApiServicePort",
    "ApiProviderPort",
    "ApiProviderRegistry",
    "ApiInvoker",
    "ApiProvider",
]