"""Service Registry for local execution - maps service names to app context attributes."""

from typing import TYPE_CHECKING, Any
import warnings

from .unified_service_registry import UnifiedServiceRegistry

if TYPE_CHECKING:
    from .context import ApplicationContext


class LocalServiceRegistry(UnifiedServiceRegistry):
    """Maps service names to application context attributes.
    
    DEPRECATED: This class is maintained for backward compatibility.
    New code should use UnifiedServiceRegistry.from_context() directly.
    """

    def __init__(self, app_context: "ApplicationContext"):
        """Initialize with app context."""
        warnings.warn(
            "LocalServiceRegistry is deprecated. Use UnifiedServiceRegistry.from_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.app_context = app_context
        
        # Initialize as a UnifiedServiceRegistry from context
        registry = UnifiedServiceRegistry.from_context(app_context)
        super().__init__()
        
        # Copy the services from the created registry
        self._items = registry._items.copy()
        self._aliases = registry._aliases.copy()
        
        # Add additional service mappings specific to LocalServiceRegistry
        extra_mappings = {
            "llm": "llm_service",  # LocalServiceRegistry uses llm_service
            "diagram_storage": "diagram_storage_service",
            "storage": "diagram_storage_service",
            "api": "api_integration_service",
            "text": "text_processing_service",
            "text_processing": "text_processing_service",
        }
        
        for service_name, attr_name in extra_mappings.items():
            if hasattr(app_context, attr_name):
                service = getattr(app_context, attr_name)
                if service is not None and service_name not in self._items:
                    self.register(service_name, service)

    def get_service(self, service_name: str) -> Any:
        """Get a service by name, handling special cases.
        
        DEPRECATED: Use get() method instead.
        """
        warnings.warn(
            "get_service is deprecated. Use get() method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        service = self.get(service_name)
        if service is None:
            raise ValueError(
                f"Service '{service_name}' not found in application context"
            )
        return service
