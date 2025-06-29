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

    def get_handler_services(self, node_type: str) -> dict[str, Any]:
        """Return only services needed by specific handler type."""
        service_map = {
            # Person job needs conversation service
            "person_job": {"conversation": self.conversation},
            # Person batch job needs conversation and diagram storage
            "person_batch_job": {
                "conversation": self.conversation,
                "diagram_storage": self.diagram_storage,
            },
            # Notion nodes need notion integration
            "notion": {"notion": self.notion_integration},
            "notion_read": {"notion": self.notion_integration},
            "notion_save": {"notion": self.notion_integration},
            # File operations
            "file": {"file": self.file_operations},
            "file_read": {"file": self.file_operations},
            "file_save": {"file": self.file_operations},
            # Diagram operations
            "diagram": {"storage": self.diagram_storage},
            # Job nodes need LLM service directly
            "job": {"llm": self._llm_service, "api_key": self._api_key_service},
            # API nodes
            "api": {"api": self.api_integration, "file": self._file_service},
            # Text nodes
            "text": {"text": self.text_processing},
            "endpoint": {"file": self._file_service},
            "start": {},
            # Condition nodes might need file service for evaluations
            "condition": {"file": self._file_service},
            # Database nodes need db operations service
            "db": {"db_operations": self.db_operations},
        }

        return service_map.get(node_type, {})
