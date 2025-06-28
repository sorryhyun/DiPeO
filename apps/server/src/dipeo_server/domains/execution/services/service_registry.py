"""Service Registry for clean dependency injection to node handlers."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo_server.application.app_context import AppContext
    from dipeo_server.domains.conversation.domain_service import (
        ConversationDomainService,
    )
    from dipeo_server.domains.diagram.services.domain_service import (
        DiagramStorageDomainService,
    )
    from dipeo_server.infrastructure.external.integrations.notion.domain_service import (
        NotionIntegrationDomainService,
    )


class ServiceRegistry:
    """Registry that wraps infrastructure with domain-specific interfaces."""

    def __init__(self, app_context: "AppContext"):
        """Initialize registry with app context."""
        self._app = app_context

        # Lazy initialization of domain services
        self._conversation_service: ConversationDomainService | None = None
        self._notion_integration_service: NotionIntegrationDomainService | None = None
        self._diagram_storage_service: DiagramStorageDomainService | None = None
        self._api_integration_service: Any | None = None
        self._text_processing_service: Any | None = None
        self._file_operations_service: Any | None = None

    @property
    def conversation(self) -> "ConversationDomainService":
        """Get or create conversation domain service."""
        if self._conversation_service is None:
            from dipeo_server.domains.conversation.domain_service import (
                ConversationDomainService,
            )

            self._conversation_service = ConversationDomainService(
                llm_service=self._app.llm_service,
                api_key_service=self._app.api_key_service,
                conversation_service=self._app.conversation_service,
            )
        return self._conversation_service

    @property
    def notion_integration(self) -> "NotionIntegrationDomainService":
        """Get or create notion integration domain service."""
        if self._notion_integration_service is None:
            from dipeo_server.infrastructure.external.integrations.notion.domain_service import (
                NotionIntegrationDomainService,
            )

            self._notion_integration_service = NotionIntegrationDomainService(
                notion_service=self._app.notion_service,
                file_service=self._app.file_service,
            )
        return self._notion_integration_service

    @property
    def diagram_storage(self) -> "DiagramStorageDomainService":
        """Get or create diagram storage domain service."""
        if self._diagram_storage_service is None:
            from dipeo_server.domains.diagram.services.domain_service import (
                DiagramStorageDomainService,
            )

            self._diagram_storage_service = DiagramStorageDomainService(
                storage_service=self._app.diagram_storage_service
            )
        return self._diagram_storage_service

    @property
    def api_integration(self) -> Any:
        """Get or create API integration domain service."""
        if self._api_integration_service is None:
            # Check if UnifiedAppContext is being used
            if hasattr(self._app, "api_integration_service"):
                self._api_integration_service = self._app.api_integration_service
        return self._api_integration_service

    @property
    def text_processing(self) -> Any:
        """Get or create text processing domain service."""
        if self._text_processing_service is None:
            # Check if UnifiedAppContext is being used
            if hasattr(self._app, "text_processing_service"):
                self._text_processing_service = self._app.text_processing_service
        return self._text_processing_service

    @property
    def file_operations(self) -> Any:
        """Get or create file operations domain service."""
        if self._file_operations_service is None:
            # Check if UnifiedAppContext is being used
            if hasattr(self._app, "file_operations_service"):
                self._file_operations_service = self._app.file_operations_service
        return self._file_operations_service

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
            # File operations - use new domain service if available
            "file": {"file": self.file_operations or self._app.file_service},
            "file_read": {"file": self.file_operations or self._app.file_service},
            "file_save": {"file": self.file_operations or self._app.file_service},
            # Diagram operations
            "diagram": {"storage": self.diagram_storage},
            # Job nodes need LLM service directly
            "job": {"llm": self._app.llm_service, "api_key": self._app.api_key_service},
            # API nodes use new API integration service if available
            "api": {"api": self.api_integration, "file": self._app.file_service},
            # Text nodes use new text processing service if available
            "text": {"text": self.text_processing},
            "endpoint": {"file": self._app.file_service},
            "start": {},
            # Condition nodes might need file service for evaluations
            "condition": {"file": self._app.file_service},
            # Database nodes need file service
            "db": {"file": self._app.file_service},
        }

        return service_map.get(node_type, {})
