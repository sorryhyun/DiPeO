"""Adapters that bridge existing API infrastructure to new domain ports."""

from typing import Any, Optional

from dipeo.core.ports import IntegratedApiServicePort
from dipeo.domain.integrations import ApiInvoker, ApiProvider, ApiProviderRegistry
from dipeo.infrastructure.services.integrated_api.service import IntegratedApiService


class ApiProviderRegistryAdapter(ApiProviderRegistry):
    """Adapter wrapping IntegratedApiService for provider registry functionality."""

    def __init__(self, api_service: IntegratedApiServicePort | None = None):
        self._service = api_service or IntegratedApiService()
        self._providers: dict[str, ApiProvider] = {}

    async def initialize(self) -> None:
        """Initialize the service."""
        if hasattr(self._service, 'initialize'):
            await self._service.initialize()

    async def register_provider(self, provider_name: str, provider_instance: ApiProvider) -> None:
        """Register a new API provider."""
        self._providers[provider_name] = provider_instance
        
        # Also register with underlying service if it supports it
        if hasattr(self._service, 'register_provider'):
            await self._service.register_provider(provider_name, provider_instance)

    async def unregister_provider(self, provider_name: str) -> None:
        """Unregister an API provider."""
        self._providers.pop(provider_name, None)
        
        if hasattr(self._service, 'unregister_provider'):
            await self._service.unregister_provider(provider_name)

    def get_provider(self, provider_name: str) -> Optional[ApiProvider]:
        """Get a registered provider by name."""
        return self._providers.get(provider_name)

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        # Get from underlying service if available
        if hasattr(self._service, 'list_providers'):
            return self._service.list_providers()
        return list(self._providers.keys())

    def get_provider_manifest(self, provider_name: str) -> Optional[dict]:
        """Get provider manifest with capabilities and schemas."""
        provider = self._providers.get(provider_name)
        if provider:
            return provider.manifest
        
        # Try underlying service
        if hasattr(self._service, 'get_provider_manifest'):
            return self._service.get_provider_manifest(provider_name)
        return None


class ApiInvokerAdapter(ApiInvoker):
    """Adapter implementing ApiInvoker using IntegratedApiService."""

    def __init__(self, api_service: IntegratedApiServicePort | None = None):
        self._service = api_service or IntegratedApiService()

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
        """Invoke an API operation with automatic auth and retries."""
        # Use the underlying service's execute_operation
        return await self._service.execute_operation(
            provider=provider,
            operation=operation,
            config=config or {},
            resource_id=resource_id,
            api_key_id=api_key_id or "default",
        )

    async def validate_operation(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Validate if an operation can be executed."""
        try:
            # Try to get the provider and check if operation is supported
            if hasattr(self._service, 'get_provider_capabilities'):
                capabilities = await self._service.get_provider_capabilities(provider)
                return operation in capabilities.get("operations", [])
            
            # Fallback: try to prepare the request and see if it succeeds
            await self.prepare_request(provider, operation, config)
            return True
        except Exception:
            return False

    async def prepare_request(
        self,
        provider: str,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        api_key_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Prepare request with auth headers and transformed config."""
        # This would typically transform the config and add auth headers
        prepared = {
            "provider": provider,
            "operation": operation,
            "config": config or {},
            "headers": {},
        }
        
        # Add auth if available
        if api_key_id and hasattr(self._service, 'api_key_service'):
            try:
                api_key = self._service.api_key_service.get_api_key(api_key_id)
                prepared["headers"]["Authorization"] = f"Bearer {api_key['key']}"
            except Exception:
                pass
        
        return prepared

    async def map_response(
        self,
        provider: str,
        operation: str,
        response: Any,
    ) -> dict[str, Any]:
        """Map provider-specific response to standard format."""
        # Standard response mapping
        if isinstance(response, dict):
            return response
        
        return {
            "success": True,
            "data": response,
            "provider": provider,
            "operation": operation,
        }


class SimpleApiProvider(ApiProvider):
    """Simple implementation of ApiProvider for testing."""

    def __init__(self, name: str, operations: list[str] | None = None):
        self._name = name
        self._operations = operations or ["test", "echo", "ping"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_operations(self) -> list[str]:
        return self._operations

    @property
    def manifest(self) -> dict:
        return {
            "name": self.name,
            "version": "1.0.0",
            "operations": self.supported_operations,
            "schemas": {
                op: {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string"},
                    },
                }
                for op in self.supported_operations
            },
        }

    async def execute(
        self,
        operation: str,
        config: Optional[dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> Any:
        """Execute an operation."""
        if operation not in self.supported_operations:
            raise ValueError(f"Operation {operation} not supported")
        
        # Simple echo implementation
        if operation == "echo":
            return config or {"echo": "response"}
        elif operation == "ping":
            return {"status": "pong", "timestamp": str(datetime.now())}
        elif operation == "test":
            return {"success": True, "data": config}
        
        return {"operation": operation, "config": config}

    async def validate_config(
        self, operation: str, config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Validate operation configuration."""
        return operation in self.supported_operations

    def get_operation_schema(self, operation: str) -> Optional[dict]:
        """Get JSON schema for operation configuration."""
        if operation in self.supported_operations:
            return self.manifest["schemas"].get(operation)
        return None


# Import datetime for the provider
from datetime import datetime