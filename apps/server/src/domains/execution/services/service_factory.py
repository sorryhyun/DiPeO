"""Service factory for dependency injection in executors."""
from typing import Dict, Any, Optional, Protocol, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.domains.llm.service import LLMService
    from src.domains.memory.services.memory_service import MemoryService
    from src.domains.person.services.person_service import PersonService
    from src.domains.code_execution.services.code_execution_service import CodeExecutionService
    from src.domains.file.services.file_service import FileService
    from src.domains.integrations.notion.services.notion_service import NotionService
    from src.domains.execution.services.user_interaction_service import UserInteractionService


class ServiceProvider(Protocol):
    """Protocol for service providers."""
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name."""
        ...


@dataclass
class ServiceRegistry:
    """Registry of available services for executors."""
    llm_service: Optional['LLMService'] = None
    memory_service: Optional['MemoryService'] = None
    person_service: Optional['PersonService'] = None
    code_execution_service: Optional['CodeExecutionService'] = None
    file_service: Optional['FileService'] = None
    notion_service: Optional['NotionService'] = None
    user_interaction_service: Optional['UserInteractionService'] = None
    interactive_handler: Optional[Any] = None
    
    # Additional services can be registered here
    _custom_services: Dict[str, Any] = field(default_factory=dict)
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name."""
        # Check standard services first
        if hasattr(self, service_name):
            return getattr(self, service_name)
        # Check custom services
        return self._custom_services.get(service_name)
    
    def register_service(self, name: str, service: Any):
        """Register a custom service."""
        if hasattr(self, name):
            # Standard service
            setattr(self, name, service)
        else:
            # Custom service
            self._custom_services[name] = service
    
    def get_required_services(self, service_names: list[str]) -> Dict[str, Any]:
        """Get multiple services by name."""
        services = {}
        for name in service_names:
            service = self.get_service(name)
            if service is not None:
                services[name] = service
        return services


class ServiceFactory:
    """Factory for creating service instances and managing dependencies."""
    
    def __init__(self):
        self._registry = ServiceRegistry()
        self._initializers: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any):
        """Register a service instance."""
        self._registry.register_service(name, service)
    
    def register_initializer(self, name: str, initializer: Any):
        """Register a service initializer function."""
        self._initializers[name] = initializer
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name, initializing if needed."""
        service = self._registry.get_service(name)
        if service is None and name in self._initializers:
            # Initialize service on demand
            service = self._initializers[name]()
            self._registry.register_service(name, service)
        return service
    
    def get_registry(self) -> ServiceRegistry:
        """Get the current service registry."""
        return self._registry
    
    def create_context_services(self, required_services: list[str]) -> Dict[str, Any]:
        """Create a dictionary of services for a specific context."""
        return self._registry.get_required_services(required_services)


# Global service factory instance
service_factory = ServiceFactory()