"""
Service Registry Protocol for dependency injection.

This protocol defines the interface for service registries used throughout
the DiPeO application layer, providing a type-safe contract for service access.
"""

from typing import Protocol, Any, Optional, List


class ServiceRegistryProtocol(Protocol):
    """Protocol defining the interface for service registries.
    
    This protocol ensures consistent service access patterns across different
    registry implementations, whether they're used in server mode, CLI mode,
    or test environments.
    """
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service by name.
        
        Args:
            name: The name of the service to retrieve
            
        Returns:
            The service instance if found, None otherwise
        """
        ...
    
    def has(self, name: str) -> bool:
        """Check if a service is registered.
        
        Args:
            name: The name of the service to check
            
        Returns:
            True if the service is registered, False otherwise
        """
        ...
    
    def register(self, name: str, item: Any) -> None:
        """Register a service.
        
        Args:
            name: The name to register the service under
            item: The service instance to register
        """
        ...
    
    def unregister(self, name: str) -> None:
        """Unregister a service.
        
        Args:
            name: The name of the service to unregister
        """
        ...
    
    def list_items(self) -> List[str]:
        """List all registered service names.
        
        Returns:
            A list of all registered service names
        """
        ...


class TypedServiceRegistryProtocol(ServiceRegistryProtocol, Protocol):
    """Extended protocol for type-safe service registries.
    
    This protocol extends the base ServiceRegistryProtocol to provide
    type information for specific services commonly used in DiPeO.
    """
    
    @property
    def llm_service(self) -> Any:
        """LLM service for language model interactions."""
        ...
    
    @property
    def api_key_service(self) -> Any:
        """API key management service."""
        ...
    
    @property
    def file_service(self) -> Any:
        """File operations service."""
        ...
    
    @property
    def memory_service(self) -> Any:
        """Memory/cache service."""
        ...
    
    @property
    def conversation_service(self) -> Any:
        """Conversation management service."""
        ...
    
    @property
    def notion_service(self) -> Any:
        """Notion integration service."""
        ...
    
    @property
    def api_integration_service(self) -> Any:
        """External API integration service."""
        ...
    
    @property
    def diagram_loader(self) -> Any:
        """Diagram loading service."""
        ...
    
    @property
    def diagram_storage_service(self) -> Any:
        """Diagram storage domain service."""
        ...
    
    @property
    def text_processing_service(self) -> Any:
        """Text processing domain service."""
        ...
    
    @property
    def db_operations_service(self) -> Any:
        """Database operations service."""
        ...
    
    @property
    def execution_flow_service(self) -> Any:
        """Execution flow control service."""
        ...
    
    @property
    def input_resolution_service(self) -> Any:
        """Input resolution service."""
        ...