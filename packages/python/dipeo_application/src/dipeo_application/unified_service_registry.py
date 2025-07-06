"""Unified service registry that works for both server and local execution."""

from typing import Any, Dict, List, Optional

from dipeo_core.utils.dynamic_registry import DynamicRegistry


class UnifiedServiceRegistry(DynamicRegistry):
    """Unified service registry that supports both static and dynamic service registration.
    
    This registry can be used in multiple contexts:
    1. Server mode: Services are injected via constructor
    2. Local/CLI mode: Services are provided via ApplicationContext
    3. Test mode: Services can be registered dynamically
    
    Example:
        # Server mode
        registry = UnifiedServiceRegistry(
            llm=llm_service,
            file=file_service,
            memory=memory_service
        )
        
        # Local mode
        registry = UnifiedServiceRegistry.from_context(app_context)
        
        # Dynamic mode
        registry = UnifiedServiceRegistry()
        registry.register("llm", llm_service)
    """
    
    def __init__(self, **services):
        """Initialize with optional services.
        
        Args:
            **services: Services to register immediately
        """
        super().__init__()
        
        # Register any provided services
        for name, service in services.items():
            self.register(name, service)
    
    @classmethod
    def from_context(cls, context: Any) -> "UnifiedServiceRegistry":
        """Create registry from an ApplicationContext.
        
        This factory method is used for local/CLI execution where services
        are accessed through the ApplicationContext interface.
        
        Args:
            context: ApplicationContext instance
            
        Returns:
            UnifiedServiceRegistry configured for local execution
        """
        registry = cls()
        
        # Map of service names to context attributes
        service_mapping = {
            "file": "file_service",
            "llm": "conversation_service",
            "memory": "memory_service",
            "api_key": "api_key_service",
            "notion": "notion_service",
            "diagram": "diagram_storage_service",
            "conversation": "conversation_service",
            "memory_service": "memory_service",  # Alias
            "api_integration": "api_integration_service",
            "code_execution": "code_execution_service",
        }
        
        # Register services from context
        for service_name, context_attr in service_mapping.items():
            if hasattr(context, context_attr):
                service = getattr(context, context_attr)
                if service is not None:
                    registry.register(service_name, service)
        
        # Add context itself for handlers that need it
        registry.register("context", context)
        registry.register("app_context", context)
        
        return registry
    
    def get_handler_services(self, required_services: List[str]) -> Dict[str, Any]:
        """Get services required by a handler.
        
        Args:
            required_services: List of service names required by the handler
            
        Returns:
            Dictionary mapping service names to service instances
            
        Raises:
            ValueError: If a required service is not available
        """
        services = {}
        
        for service_name in required_services:
            service = self.get(service_name)
            if service is None:
                raise ValueError(f"Required service '{service_name}' not found in registry")
            services[service_name] = service
        
        return services
    
    def merge(self, other: "UnifiedServiceRegistry") -> None:
        """Merge another registry into this one.
        
        This is useful for combining registries from different sources.
        
        Args:
            other: Another UnifiedServiceRegistry to merge
        """
        for name in other._items:
            if name not in self._items:
                self.register(name, other._items[name])
        
        for alias, target in other._aliases.items():
            if alias not in self._aliases and target in self._items:
                self.create_alias(alias, target)
    
    def clone(self) -> "UnifiedServiceRegistry":
        """Create a copy of this registry.
        
        Returns:
            A new UnifiedServiceRegistry with the same services
        """
        clone = UnifiedServiceRegistry()
        clone._items = self._items.copy()
        clone._aliases = self._aliases.copy()
        return clone
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        services = list(self._items.keys())
        return f"UnifiedServiceRegistry({', '.join(services)})"