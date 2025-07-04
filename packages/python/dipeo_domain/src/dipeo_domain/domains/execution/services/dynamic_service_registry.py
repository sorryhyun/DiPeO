"""Dynamic Service Registry with automatic property generation."""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from dipeo_core import (
        SupportsAPIKey,
        SupportsFile,
        SupportsLLM,
        SupportsMemory,
        SupportsNotion,
    )
    from dipeo_domain.domains.api import APIIntegrationDomainService
    from dipeo_domain.domains.diagram.services.domain_service import (
        DiagramStorageDomainService,
    )
    from dipeo_domain.domains.file import FileOperationsDomainService
    from dipeo_domain.domains.text import TextProcessingDomainService
    from dipeo_domain.domains.validation import ValidationDomainService
    from dipeo_domain.domains.db import DBOperationsDomainService


class DynamicServiceRegistry:
    """Registry that provides domain services with dynamic attribute resolution."""

    # Map property names to internal service attribute names
    _property_map = {
        # Domain service properties
        "notion": "_notion_service",
        "diagram_storage": "_diagram_storage_service",
        "api_integration": "_api_integration_service",
        "text_processing": "_text_processing_service",
        "file_operations": "_file_operations_service",
        "validation": "_validation_service",
        "db_operations": "_db_operations_service",
        # Core service properties (for get_handler_services)
        "llm": "_llm_service",
        "api_key": "_api_key_service",
        "file": "_file_service",
        "conversation_memory": "_conversation_memory_service",
    }

    def __init__(
        self,
        # Core services
        llm_service: "SupportsLLM",
        api_key_service: "SupportsAPIKey",
        file_service: "SupportsFile",
        conversation_memory_service: "SupportsMemory",
        # Domain services
        notion_service: "SupportsNotion",
        diagram_storage_service: "DiagramStorageDomainService",
        api_integration_service: "APIIntegrationDomainService",
        text_processing_service: "TextProcessingDomainService",
        file_operations_service: "FileOperationsDomainService",
        validation_service: "ValidationDomainService",
        db_operations_service: "DBOperationsDomainService",
    ):
        """Initialize registry with explicit service dependencies."""
        # Store all services in a single dict for easier dynamic access
        self._services: Dict[str, Any] = {
            "_llm_service": llm_service,
            "_api_key_service": api_key_service,
            "_file_service": file_service,
            "_conversation_memory_service": conversation_memory_service,
            "_notion_service": notion_service,
            "_diagram_storage_service": diagram_storage_service,
            "_api_integration_service": api_integration_service,
            "_text_processing_service": text_processing_service,
            "_file_operations_service": file_operations_service,
            "_validation_service": validation_service,
            "_db_operations_service": db_operations_service,
        }

    def __getattr__(self, name: str) -> Any:
        """Dynamically resolve service properties."""
        # Check if this is a known property name
        if name in self._property_map:
            service_key = self._property_map[name]
            if service_key in self._services:
                return self._services[service_key]
        
        # Check if directly accessing internal service name
        if name in self._services:
            return self._services[name]
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def register_service(self, name: str, service: Any, property_alias: Optional[str] = None) -> None:
        """Dynamically register a new service.
        
        Args:
            name: Internal service name (e.g., '_new_service')
            service: The service instance
            property_alias: Optional public property name (e.g., 'new_service')
        """
        self._services[name] = service
        if property_alias:
            self._property_map[property_alias] = name

    def get_handler_services(self, requires_services: list[str]) -> dict[str, Any]:
        """Return services required by a handler based on its declared requirements."""
        # Service name mapping - maps from handler-declared names to actual services
        service_map = {
            # Core services (multiple aliases)
            "llm": self._services["_llm_service"],
            "llm_service": self._services["_llm_service"],
            "api_key": self._services["_api_key_service"],
            "api_key_service": self._services["_api_key_service"],
            "file": self._services["_file_service"],
            "file_service": self._services["_file_service"],
            "conversation_memory": self._services["_conversation_memory_service"],
            "conversation_memory_service": self._services["_conversation_memory_service"],
            # Domain services
            "conversation": self._services["_conversation_memory_service"],
            "notion": self.notion,
            "notion_service": self.notion,
            "diagram_storage": self.diagram_storage,
            "storage": self.diagram_storage,
            "api": self.api_integration,
            "api_integration": self.api_integration,
            "text": self.text_processing,
            "text_processing": self.text_processing,
            "file_operations": self.file_operations,
            "validation": self.validation,
            "db_operations": self.db_operations,
        }

        # Build the services dict based on requirements
        services = {}
        for service_name in requires_services:
            if service_name in service_map:
                services[service_name] = service_map[service_name]
            else:
                # Log warning or raise error for unknown service
                raise ValueError(f"Unknown service requested: {service_name}")

        return services

    def list_available_services(self) -> Dict[str, str]:
        """List all available services and their property names."""
        result = {}
        # Add property aliases
        for prop_name, internal_name in self._property_map.items():
            if internal_name in self._services:
                result[prop_name] = f"Property alias for {internal_name}"
        
        # Add internal service names
        for internal_name in self._services:
            result[internal_name] = "Internal service reference"
        
        return result


# Create a factory function to easily convert existing ServiceRegistry to dynamic version
def create_dynamic_registry(service_registry: Any) -> DynamicServiceRegistry:
    """Create a DynamicServiceRegistry from an existing ServiceRegistry instance."""
    return DynamicServiceRegistry(
        llm_service=service_registry._llm_service,
        api_key_service=service_registry._api_key_service,
        file_service=service_registry._file_service,
        conversation_memory_service=service_registry._conversation_memory_service,
        notion_service=service_registry._notion_service,
        diagram_storage_service=service_registry._diagram_storage_service,
        api_integration_service=service_registry._api_integration_service,
        text_processing_service=service_registry._text_processing_service,
        file_operations_service=service_registry._file_operations_service,
        validation_service=service_registry._validation_service,
        db_operations_service=service_registry._db_operations_service,
    )