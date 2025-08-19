"""Domain ports for integrated API services."""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ApiProviderRegistry(Protocol):
    """Registry for dynamic API provider management."""

    async def register_provider(self, provider_name: str, provider_instance: "ApiProvider") -> None:
        """Register a new API provider dynamically.
        
        Args:
            provider_name: Unique identifier for the provider
            provider_instance: The provider implementation
        """
        ...

    async def unregister_provider(self, provider_name: str) -> None:
        """Unregister an API provider.
        
        Args:
            provider_name: Provider to remove
        """
        ...

    def get_provider(self, provider_name: str) -> Optional["ApiProvider"]:
        """Get a registered provider by name.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            Provider instance or None if not found
        """
        ...

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        ...

    def get_provider_manifest(self, provider_name: str) -> Optional[dict]:
        """Get provider manifest with capabilities and schemas.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            Provider manifest or None if not found
        """
        ...


@runtime_checkable
class ApiInvoker(Protocol):
    """Service for invoking API operations with authentication."""

    async def invoke(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Invoke an API operation with automatic auth and retries.
        
        Args:
            provider: Provider name from registry
            operation: Operation identifier
            config: Operation-specific configuration
            resource_id: Optional resource identifier
            api_key_id: API key identifier for auth
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            
        Returns:
            Operation result
            
        Raises:
            ProviderNotFoundError: Provider not registered
            OperationNotSupportedError: Operation not available
            AuthenticationError: API key issues
            ServiceError: Execution failures
        """
        ...

    async def validate_operation(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Validate if an operation can be executed.
        
        Args:
            provider: Provider name
            operation: Operation identifier
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...

    async def prepare_request(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        api_key_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare request with auth headers and transformed config.
        
        Args:
            provider: Provider name
            operation: Operation identifier
            config: Raw configuration
            api_key_id: API key identifier
            
        Returns:
            Prepared request data
        """
        ...

    async def map_response(
        self,
        provider: str,
        operation: str,
        response: Any,
    ) -> dict[str, Any]:
        """Map provider-specific response to standard format.
        
        Args:
            provider: Provider name
            operation: Operation identifier
            response: Raw provider response
            
        Returns:
            Standardized response
        """
        ...


@runtime_checkable
class ApiProvider(Protocol):
    """Individual API provider interface."""

    @property
    def name(self) -> str:
        """Provider unique name."""
        ...

    @property
    def supported_operations(self) -> list[str]:
        """List of supported operation identifiers."""
        ...

    @property
    def manifest(self) -> dict:
        """Provider manifest with schemas and capabilities."""
        ...

    async def execute(
        self,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> Any:
        """Execute an operation.
        
        Args:
            operation: Operation identifier
            config: Operation configuration
            resource_id: Optional resource ID
            headers: Request headers (including auth)
            timeout: Request timeout
            
        Returns:
            Provider-specific response
            
        Raises:
            OperationError: On execution failures
        """
        ...

    async def validate_config(
        self, operation: str, config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Validate operation configuration.
        
        Args:
            operation: Operation identifier
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        ...

    def get_operation_schema(self, operation: str) -> Optional[dict]:
        """Get JSON schema for operation configuration.
        
        Args:
            operation: Operation identifier
            
        Returns:
            JSON schema or None
        """
        ...