"""Local application context for CLI execution."""

import logging
from typing import Any

from dipeo_application import MinimalMessageRouter, MinimalStateStore
from dipeo_core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)
from dipeo_application import ApplicationContext
from dipeo_infra.external.apikey import EnvironmentAPIKeyService

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

    async def initialize_for_local(self):
        """Initialize minimal services for local execution."""
        # Import necessary services
        from dipeo_application import LocalExecutionService
        from dipeo_infra import ConsolidatedFileService, LLMInfraService, MemoryService

        # Initialize API key service with environment variables
        self._api_key_service = EnvironmentAPIKeyService()
        await self._api_key_service.initialize()

        # Initialize LLM service using server's implementation
        self._llm_service = LLMInfraService(self._api_key_service)
        await self._llm_service.initialize()
        
        # Initialize memory service
        self._memory_service = MemoryService()
        
        # Set conversation_service to memory_service (as per ApplicationContext protocol)
        self._conversation_service = self._memory_service

        self._file_service = ConsolidatedFileService()

        # Initialize execution service
        self._execution_service = LocalExecutionService(self)
        await self._execution_service.initialize()

        logger.info(
            "Local context initialized with server's LLM service using environment variables"
        )
