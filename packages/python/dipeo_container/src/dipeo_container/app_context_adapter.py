"""Adapter to provide AppContext interface using DI container."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .container import Container


class AppContextAdapter:
    """
    Adapter that provides the same interface as the original AppContext
    but delegates to the DI container for service resolution.
    """

    def __init__(self, container: "Container"):
        if container is None:
            raise ValueError("Container cannot be None in AppContextAdapter")
        self._container = container

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to container providers.

        This allows code that expects app_context.service_name to work
        without modification.
        """
        # Map attribute names to container provider names
        provider_map = {
            "api_key_service": "api_key_service",
            "llm_service": "llm_service",
            "file_service": "file_service",
            "conversation_service": "conversation_service",
            "execution_service": "execution_service",
            "notion_service": "notion_service",
            "diagram_storage_service": "diagram_storage_service",
            "diagram_storage_adapter": "diagram_storage_adapter",
            "execution_preparation_service": "execution_preparation_service",
            "api_integration_service": "api_integration_service",
            "text_processing_service": "text_processing_service",
            "file_operations_service": "file_operations_service",
            "state_store": "state_store",
            "message_router": "message_router",
        }

        if name in provider_map:
            provider_name = provider_map[name]
            if hasattr(self._container, provider_name):
                provider = getattr(self._container, provider_name)
                # Call the provider to get the service instance
                return provider()

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    @property
    def container(self) -> "Container":
        """Access to the underlying container for advanced usage."""
        return self._container

    async def startup(self) -> None:
        """Initialize all resources (for backward compatibility)."""
        from dipeo_container.container import init_resources
        await init_resources(self._container)

    async def shutdown(self) -> None:
        """Cleanup all resources (for backward compatibility)."""
        from dipeo_container.container import shutdown_resources
        await shutdown_resources(self._container)
