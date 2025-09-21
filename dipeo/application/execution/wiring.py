"""Wiring module for execution bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from dipeo.application.registry.keys import (
    CLI_SESSION_SERVICE,
    CONVERSATION_REPOSITORY,
    EXECUTE_DIAGRAM_USE_CASE,
    EXECUTION_ORCHESTRATOR,
    PERSON_REPOSITORY,
    PREPARE_DIAGRAM_USE_CASE,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def wire_execution(registry: ServiceRegistry) -> None:
    """Wire execution bounded context services and use cases.

    This includes:
    - Execution orchestrator
    - Execute diagram use case
    - Prepare diagram use case
    - CLI session service
    - Handler auto-registration
    """
    # Ensure handlers are auto-registered
    # This import triggers the auto-registration in handlers/__init__.py
    import dipeo.application.execution.handlers

    # Wire conversation repositories (used by ExecutionOrchestrator)
    from dipeo.infrastructure.storage.conversation import (
        InMemoryConversationRepository,
        InMemoryPersonRepository,
    )

    def create_conversation_repository() -> InMemoryConversationRepository:
        return InMemoryConversationRepository()

    registry.register(CONVERSATION_REPOSITORY, create_conversation_repository)

    def create_person_repository() -> InMemoryPersonRepository:
        return InMemoryPersonRepository()

    registry.register(PERSON_REPOSITORY, create_person_repository)

    # Wire execution orchestrator
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.application.registry.keys import (
        FILESYSTEM_ADAPTER,
        LLM_SERVICE,
        PROMPT_LOADING_SERVICE,
    )

    def create_execution_orchestrator() -> ExecutionOrchestrator:
        """Factory for execution orchestrator with all dependencies."""
        person_repo = registry.resolve(PERSON_REPOSITORY)
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY)

        # Create PromptLoadingUseCase
        filesystem_adapter = registry.resolve(FILESYSTEM_ADAPTER)
        prompt_loading = PromptLoadingUseCase(filesystem_adapter)
        registry.register(PROMPT_LOADING_SERVICE, prompt_loading)

        # Get LLM service
        llm_service = registry.resolve(LLM_SERVICE)

        # Create orchestrator with all dependencies
        orchestrator = ExecutionOrchestrator(
            person_repository=person_repo,
            conversation_repository=conversation_repo,
            prompt_loading_use_case=prompt_loading,
            memory_selector=None,  # No longer using domain adapters
            llm_service=llm_service,
        )

        return orchestrator

    # Register execution orchestrator
    registry.register(EXECUTION_ORCHESTRATOR, lambda: create_execution_orchestrator())

    # Wire execute diagram use case
    from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase

    def create_execute_diagram() -> ExecuteDiagramUseCase:
        """Factory for execute diagram use case."""
        # ExecuteDiagramUseCase has a different constructor signature
        return ExecuteDiagramUseCase(service_registry=registry)

    # Register execute diagram use case
    registry.register(EXECUTE_DIAGRAM_USE_CASE, create_execute_diagram)

    # Wire prepare diagram use case
    from dipeo.application.execution.use_cases.prepare_diagram import (
        PrepareDiagramForExecutionUseCase,
    )
    from dipeo.application.registry.keys import API_KEY_SERVICE

    def create_prepare_diagram() -> PrepareDiagramForExecutionUseCase:
        """Factory for prepare diagram use case."""
        api_key_service = registry.resolve(API_KEY_SERVICE)
        return PrepareDiagramForExecutionUseCase(
            api_key_service=api_key_service, service_registry=registry
        )

    # Register prepare diagram use case
    registry.register(PREPARE_DIAGRAM_USE_CASE, create_prepare_diagram)

    # Wire CLI session service
    from dipeo.application.execution.use_cases.cli_session import CliSessionService

    def create_cli_session_service() -> CliSessionService:
        """Factory for CLI session service."""
        return CliSessionService()

    # Register CLI session service
    registry.register(CLI_SESSION_SERVICE, create_cli_session_service)
