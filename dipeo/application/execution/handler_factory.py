"""Handler factory with dependency injection support."""

from typing import Any, Callable, Dict, Type

from .handlers import BaseNodeHandler
from ..unified_service_registry import UnifiedServiceRegistry


class HandlerFactory:
    """Factory for creating handler instances with injected dependencies."""
    
    def __init__(self, service_registry: UnifiedServiceRegistry):
        self.service_registry = service_registry
        self._handler_classes: Dict[str, Type[BaseNodeHandler]] = {}
        
    def register_handler_class(self, handler_class: Type[BaseNodeHandler]) -> None:
        """Register a handler class for later instantiation."""
        # Create a temporary instance to get the node_type
        temp_instance = handler_class()
        node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class
        
    def create_handler(self, node_type: str) -> BaseNodeHandler:
        """Create a handler instance with injected services."""
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            raise ValueError(f"No handler registered for node type: {node_type}")
            
        # Check if the handler has been updated to use constructor injection
        # by looking at its __init__ signature
        import inspect
        sig = inspect.signature(handler_class.__init__)
        params = list(sig.parameters.keys())
        
        # If it only has 'self', it's the old style
        if len(params) == 1 and params[0] == 'self':
            # Old style handler - create without services
            return handler_class()
        else:
            # New style handler - inject services
            return self._create_handler_with_services(handler_class)
            
    def _create_handler_with_services(self, handler_class: Type[BaseNodeHandler]) -> BaseNodeHandler:
        """Create a handler instance with services based on its constructor signature."""
        import inspect
        
        sig = inspect.signature(handler_class.__init__)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            # Try to get the service from the registry
            service_name = param_name
            
            # Handle special mappings
            if service_name == 'template_service':
                service_name = 'template'
            elif service_name == 'conversation_service':
                service_name = 'conversation_service'
            
            try:
                service = self.service_registry.get_service(service_name)
                kwargs[param_name] = service
            except:
                # If service not found and parameter has no default, this will fail
                if param.default is inspect.Parameter.empty:
                    # Try alternative names
                    if service_name.endswith('_service'):
                        # Try without _service suffix
                        alt_name = service_name[:-8]
                        try:
                            service = self.service_registry.get_service(alt_name)
                            kwargs[param_name] = service
                            continue
                        except:
                            pass
                    raise ValueError(f"Required service '{service_name}' not found for handler {handler_class.__name__}")
                    
        return handler_class(**kwargs)


def create_handler_factory_provider():
    """Provider function for DI container."""
    def factory(service_registry: UnifiedServiceRegistry) -> HandlerFactory:
        return HandlerFactory(service_registry)
    return factory