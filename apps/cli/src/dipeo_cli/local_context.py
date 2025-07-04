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
from dipeo_infra.external.apikey import EnvironmentAPIKeyService

logger = logging.getLogger(__name__)


class LocalAppContext:
    """Minimal application context for CLI local execution."""

    def __init__(self):
        # Required services - will be None for minimal local execution
        self.api_key_service: SupportsAPIKey | None = None
        self.llm_service: SupportsLLM | None = None
        self.file_service: SupportsFile | None = None
        self.memory_service: SupportsMemory | None = (
            None  # Changed from conversation_service
        )
        self.conversation_service: Any | None = (
            None  # Will be SimpleConversationService
        )
        self.execution_service: SupportsExecution | None = None
        self.notion_service: SupportsNotion | None = None
        self.diagram_storage_service: SupportsDiagram | None = None

        # Minimal infrastructure
        self.state_store = MinimalStateStore()
        self.message_router = MinimalMessageRouter()

    async def initialize_for_local(self):
        """Initialize minimal services for local execution."""
        # Import necessary services
        from dipeo_application import LocalExecutionService
        from dipeo_infra import ConsolidatedFileService, LLMInfraService, MemoryService

        # Initialize API key service with environment variables
        self.api_key_service = EnvironmentAPIKeyService()
        await self.api_key_service.initialize()

        # Initialize LLM service using server's implementation
        self.llm_service = LLMInfraService(self.api_key_service)
        await self.llm_service.initialize()

        self.memory_service = MemoryService()
        self.file_service = ConsolidatedFileService()

        # TODO: Initialize conversation service when it's updated to use correct domain models
        # For now, we'll use None which means person_job nodes won't work in local mode
        self.conversation_service = None

        # Initialize execution service
        self.execution_service = LocalExecutionService(self)
        await self.execution_service.initialize()

        logger.info(
            "Local context initialized with server's LLM service using environment variables"
        )
