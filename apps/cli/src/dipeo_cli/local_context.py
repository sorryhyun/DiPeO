"""Local application context for CLI execution."""

import logging
from typing import Any

from dipeo.application import MinimalMessageRouter, MinimalStateStore
from dipeo.core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)
from dipeo.infra.external.apikey import EnvironmentAPIKeyService

logger = logging.getLogger(__name__)


class LocalAppContext:
    """Minimal application context for CLI local execution."""

    def __init__(self):
        # Required services - will be None for minimal local execution
        self._api_key_service: SupportsAPIKey | None = None
        self._llm_service: SupportsLLM | None = None
        self._conversation_service: SupportsMemory | None = None  # Note: Should be SupportsMemory per protocol
        self._file_service: SupportsFile | None = None
        self._memory_service: SupportsMemory | None = None
        self._execution_service: SupportsExecution | None = None
        self._notion_service: SupportsNotion | None = None
        self._diagram_storage_service: SupportsDiagram | None = None
        self._db_operations_service: Any | None = None
        self._text_processing_service: Any | None = None
        self._api_integration_service: Any | None = None
        self._code_execution_service: Any | None = None

        # Minimal infrastructure
        self._state_store = MinimalStateStore()
        self._message_router = MinimalMessageRouter()
    
    # Properties to match ApplicationContext protocol
    @property
    def api_key_service(self) -> SupportsAPIKey | None:
        return self._api_key_service
    
    @property
    def llm_service(self) -> SupportsLLM | None:
        return self._llm_service
    
    @property
    def conversation_service(self) -> SupportsMemory | None:
        return self._conversation_service
    
    @property
    def file_service(self) -> SupportsFile | None:
        return self._file_service
    
    @property 
    def memory_service(self) -> SupportsMemory | None:
        return self._memory_service
    
    @property
    def execution_service(self) -> SupportsExecution | None:
        return self._execution_service
    
    @property
    def notion_service(self) -> SupportsNotion | None:
        return self._notion_service
    
    @property
    def diagram_storage_service(self) -> SupportsDiagram | None:
        return self._diagram_storage_service
    
    @property
    def state_store(self):
        return self._state_store
    
    @property
    def message_router(self):
        return self._message_router
    
    @property
    def db_operations_service(self) -> Any | None:
        return self._db_operations_service
    
    @property
    def text_processing_service(self) -> Any | None:
        return self._text_processing_service
    
    @property
    def api_integration_service(self) -> Any | None:
        return self._api_integration_service
    
    @property
    def code_execution_service(self) -> Any | None:
        return self._code_execution_service

    async def initialize_for_local(self):
        """Initialize minimal services for local execution."""
        # Import necessary services
        from dipeo.application import LocalExecutionService
        from dipeo.infra import ConsolidatedFileService, LLMInfraService, MemoryService
        from dipeo.domain.services.db import DBOperationsDomainService
        from dipeo.domain.services.validation import ValidationDomainService
        from dipeo.domain.services.text import TextProcessingDomainService
        from dipeo.domain.services.api import APIIntegrationDomainService

        # Initialize API key service with environment variables
        self._api_key_service = EnvironmentAPIKeyService()
        await self._api_key_service.initialize()

        # Initialize LLM service using server's implementation
        self._llm_service = LLMInfraService(self._api_key_service)
        await self._llm_service.initialize()
        
        # Initialize memory service
        self._memory_service = MemoryService()
        
        # Initialize conversation memory service
        from dipeo.domain.services.conversation import ConversationMemoryService
        self._conversation_service = ConversationMemoryService(memory_service=self._memory_service)

        self._file_service = ConsolidatedFileService()

        # Initialize domain services
        validation_service = ValidationDomainService()
        self._db_operations_service = DBOperationsDomainService(
            file_service=self._file_service,
            validation_service=validation_service
        )
        
        self._text_processing_service = TextProcessingDomainService()
        
        self._api_integration_service = APIIntegrationDomainService(
            file_service=self._file_service
        )

        # Initialize execution service
        self._execution_service = LocalExecutionService(self)
        await self._execution_service.initialize()

        logger.info(
            "Local context initialized with server's LLM service using environment variables"
        )
