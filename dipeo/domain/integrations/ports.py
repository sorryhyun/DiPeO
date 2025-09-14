"""Domain ports for integrated API services."""

from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.diagram_generated import ChatResult


@runtime_checkable
class ApiProviderRegistry(Protocol):
    """Registry for dynamic API provider management."""

    async def register_provider(self, provider_name: str, provider_instance: "ApiProvider") -> None:
        """Register a new API provider dynamically."""
        ...

    async def unregister_provider(self, provider_name: str) -> None:
        """Unregister an API provider."""
        ...

    def get_provider(self, provider_name: str) -> Optional["ApiProvider"]:
        """Get a registered provider by name."""
        ...

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        ...

    def get_provider_manifest(self, provider_name: str) -> dict | None:
        """Get provider manifest with capabilities and schemas."""
        ...


@runtime_checkable
class ApiInvoker(Protocol):
    """Service for invoking API operations with authentication."""

    async def invoke(
        self,
        provider: str,
        operation: str,
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        api_key_id: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Invoke an API operation with automatic auth and retries."""
        ...

    async def validate_operation(
        self,
        provider: str,
        operation: str,
        config: dict[str, Any] | None = None,
    ) -> bool:
        """Validate if an operation can be executed."""
        ...

    async def prepare_request(
        self,
        provider: str,
        operation: str,
        config: dict[str, Any] | None = None,
        api_key_id: str | None = None,
    ) -> dict[str, Any]:
        """Prepare request with auth headers and transformed config."""
        ...

    async def map_response(
        self,
        provider: str,
        operation: str,
        response: Any,
    ) -> dict[str, Any]:
        """Map provider-specific response to standard format."""
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
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Execute an operation."""
        ...

    async def validate_config(self, operation: str, config: dict[str, Any] | None = None) -> bool:
        """Validate operation configuration."""
        ...

    def get_operation_schema(self, operation: str) -> dict | None:
        """Get JSON schema for operation configuration."""
        ...


class APIKeyPort(Protocol):
    """Protocol for API key management."""

    async def get_api_key(self, key_name: str) -> str | None:
        """Get an API key by name."""
        ...

    async def set_api_key(self, key_name: str, key_value: str) -> None:
        """Set an API key."""
        ...

    async def delete_api_key(self, key_name: str) -> None:
        """Delete an API key."""
        ...

    async def list_api_keys(self) -> list[str]:
        """List all API key names."""
        ...


class ASTParserPort(Protocol):
    """Protocol for AST parsers supporting multiple programming languages."""

    async def parse(
        self, source: str, extract_patterns: list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse source code and extract AST information."""
        ...

    async def parse_file(
        self, file_path: str, extract_patterns: list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse a file and extract AST information."""
        ...

    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple source code strings in batch."""
        ...


@runtime_checkable
class LLMService(Protocol):
    """High-level LLM service for provider selection and enrichment."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        api_key_id: str | None = None,
        **kwargs,
    ) -> "ChatResult":
        """Complete with automatic provider selection."""
        ...

    async def validate_api_key(self, api_key_id: str, provider: str | None = None) -> bool:
        """Validate an API key is functional."""
        ...

    async def get_provider_for_model(self, model: str) -> str | None:
        """Determine which provider supports a given model."""
        ...
