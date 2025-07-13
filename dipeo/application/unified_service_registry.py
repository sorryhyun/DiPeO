# Unified service registry that works for both server and local execution.

from typing import Any

from dipeo.core.utils.dynamic_registry import DynamicRegistry


class UnifiedServiceRegistry(DynamicRegistry):
    # Unified service registry that supports both static and dynamic service registration.
    # Can be used in server, local/CLI, and test modes.
    
    def __init__(self, **services):
        # Initialize with optional services.
        super().__init__()
        
        # Register any provided services
        for name, service in services.items():
            self.register(name, service)
    
    @classmethod
    def from_context(cls, context: Any) -> "UnifiedServiceRegistry":
        # Create registry from an ApplicationContext.
        registry = cls()
        
        # Map of service names to context attributes
        # Primary mappings use _service suffix consistently
        service_mapping = {
            # Core services
            "llm_service": "llm_service",
            "api_key_service": "api_key_service",
            "file_service": "file_service",
            "conversation_service": "conversation_service",
            "conversation_manager": "conversation_manager",
            "notion_service": "notion_service",
            
            # Infrastructure services
            "diagram_loader": "diagram_loader",
            "state_store": "state_store",
            "message_router": "message_router",
            
            # Domain services
            "diagram_storage_service": "diagram_storage_service",
            "api_integration_service": "api_integration_service",
            "text_processing_service": "text_processing_service",
            "db_operations_service": "db_operations_service",
            "code_execution_service": "code_execution_service",
            
            # Execution domain services
            "execution_flow_service": "execution_flow_service",
            # "input_resolution_service" removed - using typed version directly
        }
        
        # Register services from context
        for service_name, context_attr in service_mapping.items():
            if hasattr(context, context_attr):
                service = getattr(context, context_attr)
                if service is not None:
                    registry.register(service_name, service)
                    # Debug logging
                    import logging
                    logging.debug(f"Registered service: {service_name} -> {type(service).__name__}")
            else:
                # Debug logging for missing attributes
                import logging
                logging.debug(f"Context missing attribute: {context_attr}")
        
        
        # Add context itself for handlers that need it
        registry.register("context", context)
        registry.register("app_context", context)
        
        return registry
    
    def get_handler_services(self, required_services: list[str]) -> dict[str, Any]:
        # Get services required by a handler.
        services = {}
        
        for service_name in required_services:
            service = self.get(service_name)
            if service is None:
                # Special case: "diagram" is injected at runtime by execution engine
                if service_name == "diagram":
                    continue
                raise ValueError(f"Required service '{service_name}' not found in registry")
            services[service_name] = service
        
        return services
    
    def merge(self, other: "UnifiedServiceRegistry") -> None:
        # Merge another registry into this one.
        for name in other._items:
            if name not in self._items:
                self.register(name, other._items[name])
        
        for alias, target in other._aliases.items():
            if alias not in self._aliases and target in self._items:
                self.create_alias(alias, target)
    
    def clone(self) -> "UnifiedServiceRegistry":
        # Create a copy of this registry.
        clone = UnifiedServiceRegistry()
        clone._items = self._items.copy()
        clone._aliases = self._aliases.copy()
        return clone
    
    def validate_required_services(self, required_services: list[str]) -> dict[str, bool]:
        # Validate that required services are registered and available.
        validation_results = {}
        for service_name in required_services:
            service = self.get(service_name)
            validation_results[service_name] = service is not None
        return validation_results
    
    def get_health_status(self) -> dict[str, dict]:
        # Get health status of all registered services.
        health_status = {}
        for service_name, service in self._items.items():
            health_status[service_name] = {
                "registered": True,
                "type": type(service).__name__,
                "healthy": True  # Could be extended to check actual health
            }
        return health_status
    
    def __repr__(self) -> str:
        # String representation of the registry.
        services = list(self._items.keys())
        return f"UnifiedServiceRegistry({', '.join(services)})"