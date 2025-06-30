"""Service Registry for clean dependency injection to node handlers."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo_core import (
        SupportsAPIKey,
        SupportsFile,
        SupportsLLM,
        SupportsMemory,
    )
    from dipeo_infra import (
        APIIntegrationDomainService,
        NotionIntegrationDomainService,
    )

    from dipeo_domain.domains.conversation.domain_service import (
        ConversationDomainService,
    )
    from dipeo_domain.domains.diagram.services.domain_service import (
        DiagramStorageDomainService,
    )
    from dipeo_domain.domains.file import FileOperationsDomainService
    from dipeo_domain.domains.text import TextProcessingDomainService
    from dipeo_domain.domains.validation import ValidationDomainService
    from dipeo_domain.domains.db import DBOperationsDomainService


class ServiceRegistry:
    """Registry that provides domain services to node handlers with explicit dependencies."""

    def __init__(
        self,
        # Core services
        llm_service: "SupportsLLM",
        api_key_service: "SupportsAPIKey",
        file_service: "SupportsFile",
        conversation_memory_service: "SupportsMemory",
        # Domain services
        conversation_service: "ConversationDomainService",
        notion_integration_service: "NotionIntegrationDomainService",
        diagram_storage_service: "DiagramStorageDomainService",
        api_integration_service: "APIIntegrationDomainService",
        text_processing_service: "TextProcessingDomainService",
        file_operations_service: "FileOperationsDomainService",
        validation_service: "ValidationDomainService",
        db_operations_service: "DBOperationsDomainService",
    ):
        """Initialize registry with explicit service dependencies."""
        # Store core services
        self._llm_service = llm_service
        self._api_key_service = api_key_service
        self._file_service = file_service
        self._conversation_memory_service = conversation_memory_service

        # Store domain services
        self._conversation_service = conversation_service
        self._notion_integration_service = notion_integration_service
        self._diagram_storage_service = diagram_storage_service
        self._api_integration_service = api_integration_service
        self._text_processing_service = text_processing_service
        self._file_operations_service = file_operations_service
        self._validation_service = validation_service
        self._db_operations_service = db_operations_service

    @property
    def conversation(self) -> "ConversationDomainService":
        """Get conversation domain service."""
        return self._conversation_service

    @property
    def notion_integration(self) -> "NotionIntegrationDomainService":
        """Get notion integration domain service."""
        return self._notion_integration_service

    @property
    def diagram_storage(self) -> "DiagramStorageDomainService":
        """Get diagram storage domain service."""
        return self._diagram_storage_service

    @property
    def api_integration(self) -> "APIIntegrationDomainService":
        """Get API integration domain service."""
        return self._api_integration_service

    @property
    def text_processing(self) -> "TextProcessingDomainService":
        """Get text processing domain service."""
        return self._text_processing_service

    @property
    def file_operations(self) -> "FileOperationsDomainService":
        """Get file operations domain service."""
        return self._file_operations_service

    @property
    def validation(self) -> "ValidationDomainService":
        """Get validation domain service."""
        return self._validation_service

    @property
    def db_operations(self) -> "DBOperationsDomainService":
        """Get database operations domain service."""
        return self._db_operations_service

    def get_handler_services(self, requires_services: list[str]) -> dict[str, Any]:
        """Return services required by a handler based on its declared requirements."""
        # Service name mapping - maps from handler-declared names to actual services
        service_map = {
            # Core services
            "llm": self._llm_service,
            "llm_service": self._llm_service,
            "api_key": self._api_key_service,
            "api_key_service": self._api_key_service,
            "file": self._file_service,
            "file_service": self._file_service,
            "conversation_memory": self._conversation_memory_service,
            "conversation_memory_service": self._conversation_memory_service,
            
            # Domain services
            "conversation": self.conversation,
            "conversation_service": self.conversation,
            "notion": self.notion_integration,
            "notion_integration": self.notion_integration,
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
