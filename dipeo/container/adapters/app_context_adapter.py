"""Adapter to provide AppContext interface using DI container."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..container import Container


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
        # Map attribute names to their layer and provider names
        provider_map = {
            # Infrastructure services
            "state_store": ("infra", "state_store"),
            "message_router": ("infra", "message_router"),
            "file_service": ("infra", "file_service"),
            "memory_service": ("infra", "memory_service"),
            "llm_service": ("infra", "llm_service"),
            "notion_service": ("infra", "notion_service"),
            "api_service": ("infra", "api_service"),
            "file_operations_service": ("infra", "file_operations_service"),
            # Domain services
            "api_key_service": ("domain", "api_key_service"),
            "api_domain_service": ("domain", "api_domain_service"),
            "file_domain_service": ("domain", "file_domain_service"),
            "text_processing_service": ("domain", "text_processing_service"),
            "template_service": ("domain", "template_service"),
            "validation_service": ("domain", "validation_service"),
            "arrow_processor": ("domain", "arrow_processor"),
            "memory_transformer": ("domain", "memory_transformer"),
            "execution_flow_service": ("domain", "execution_flow_service"),
            "conversation_service": ("domain", "conversation_service"),
            "diagram_storage_service": ("domain", "diagram_storage_service"),
            "diagram_storage_adapter": ("domain", "diagram_storage_adapter"),
            "diagram_storage_domain_service": ("domain", "diagram_storage_domain_service"),
            "diagram_validator": ("domain", "diagram_validator"),
            "db_operations_service": ("domain", "db_operations_service"),
            "condition_evaluation_service": ("domain", "condition_evaluation_service"),
            "input_resolution_service": ("domain", "input_resolution_service"),
            "person_job_services": ("domain", "person_job_services"),
            # Application services
            "execution_preparation_service": ("application", "execution_preparation_service"),
            "service_registry": ("application", "service_registry"),
            "execution_service": ("application", "execution_service"),
            # Legacy aliases
            "api_integration_service": ("infra", "api_service"),
            "file_operations_service": ("infra", "file_operations_service"),
        }

        if name in provider_map:
            layer_name, provider_name = provider_map[name]
            layer = getattr(self._container, layer_name, None)
            if layer and hasattr(layer, provider_name):
                provider = getattr(layer, provider_name)
                # Call the provider to get the service instance
                return provider()

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    @property
    def container(self) -> "Container":
        """Access to the underlying container for advanced usage."""
        return self._container

