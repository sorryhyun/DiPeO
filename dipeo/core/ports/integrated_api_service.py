"""Integrated API Service port interface."""

from typing import Any, Protocol, runtime_checkable, Optional


@runtime_checkable
class IntegratedApiServicePort(Protocol):
    """Port interface for integrated API service supporting multiple providers."""

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
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        api_key: str | None = None,
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
        config: dict[str, Any] | None = None
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
    """Port interface for individual API providers."""

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
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        api_key: str | None = None,
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
        config: dict[str, Any] | None = None
    ) -> bool:
        """Validate operation configuration.
        
        Args:
            operation: The operation name
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...