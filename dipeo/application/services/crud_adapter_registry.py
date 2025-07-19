"""Registry for CRUD adapters that provides standard interfaces for GraphQL mutations."""

from typing import Dict, Any, Optional

from .crud_adapters import (
    CrudAdapter,
    ApiKeyCrudAdapter,
    DiagramCrudAdapter,
    ExecutionCrudAdapter
)


class CrudAdapterRegistry:
    """Registry that creates and manages CRUD adapters for services."""
    
    def __init__(self, service_registry):
        self.service_registry = service_registry
        self._adapters: Dict[str, CrudAdapter] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize standard CRUD adapters for known services."""
        # API Key adapter
        api_key_service = self.service_registry.get('api_key_service')
        if api_key_service:
            self._adapters['api_key_service'] = ApiKeyCrudAdapter(api_key_service)
        
        # Diagram adapter
        integrated_diagram_service = self.service_registry.get('integrated_diagram_service')
        diagram_storage_service = self.service_registry.get('diagram_storage_service')
        if integrated_diagram_service and diagram_storage_service:
            self._adapters['diagram_service'] = DiagramCrudAdapter(
                integrated_diagram_service,
                diagram_storage_service
            )
        
        # Note: Person, Node, Arrow, and Handle entities are all part of diagrams
        # and are edited through diagram mutations, not separate CRUD operations
        
        # Execution adapter
        execution_state_store = self.service_registry.get('state_store')
        if execution_state_store:
            self._adapters['execution_service'] = ExecutionCrudAdapter(execution_state_store)
    
    def get_adapter(self, service_name: str) -> Optional[CrudAdapter]:
        """Get a CRUD adapter by service name."""
        return self._adapters.get(service_name)
    
    def register_adapter(self, service_name: str, adapter: CrudAdapter):
        """Register a custom CRUD adapter."""
        self._adapters[service_name] = adapter
    
    def has_adapter(self, service_name: str) -> bool:
        """Check if an adapter exists for the service."""
        return service_name in self._adapters
    
    def list_adapters(self) -> Dict[str, str]:
        """List all registered adapters."""
        return {
            name: type(adapter).__name__ 
            for name, adapter in self._adapters.items()
        }


def create_crud_registry(service_registry) -> CrudAdapterRegistry:
    """Factory function to create a CRUD adapter registry."""
    return CrudAdapterRegistry(service_registry)