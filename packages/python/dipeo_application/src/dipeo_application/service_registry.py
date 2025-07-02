"""Service Registry for local execution - maps service names to app context attributes."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context import ApplicationContext


class LocalServiceRegistry:
    """Maps service names to application context attributes."""

    def __init__(self, app_context: "ApplicationContext"):
        """Initialize with app context."""
        self.app_context = app_context

    def get_service(self, service_name: str) -> Any:
        """Get a service by name, handling special cases."""
        # Service name mapping
        service_map = {
            # File services
            "file": "file_service",
            # Conversation service
            "conversation": "conversation_service",
            # LLM service
            "llm": "llm_service",
            # API key service
            "api_key": "api_key_service",
            # Diagram storage
            "diagram_storage": "diagram_storage_service",
            "storage": "diagram_storage_service",
            # API integration
            "api": "api_integration_service",
            "api_integration": "api_integration_service",
            # Text processing
            "text": "text_processing_service",
            "text_processing": "text_processing_service",
            # Notion integration
            "notion": "notion_service",
        }

        # Get the actual attribute name
        attr_name = service_map.get(service_name)
        if not attr_name:
            # If not in map, try appending _service
            attr_name = f"{service_name}_service"

        # Get the service from app context
        service = getattr(self.app_context, attr_name, None)
        if service is None:
            raise ValueError(
                f"Service '{service_name}' not found in application context"
            )

        return service

    def get_handler_services(self, requires_services: list[str]) -> dict[str, Any]:
        """Get all services required by a handler."""
        services = {}
        for service_name in requires_services:
            services[service_name] = self.get_service(service_name)
        return services
