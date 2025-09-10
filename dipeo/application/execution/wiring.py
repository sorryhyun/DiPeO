"""Wiring module for execution bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.keys import EXECUTION_ORCHESTRATOR, PREPARE_DIAGRAM_USE_CASE
from dipeo.application.registry.service_registry import ServiceKey, ServiceRegistry

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Define service keys for execution context
EXECUTE_DIAGRAM_USE_CASE = ServiceKey["ExecuteDiagramUseCase"]("execution.use_case.execute_diagram")
CLI_SESSION_USE_CASE = ServiceKey["CliSessionService"]("execution.use_case.cli_session")


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
    from dipeo.application.conversation.wiring import MANAGE_CONVERSATION_USE_CASE

    # Wire execution orchestrator
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.application.registry.keys import (
        FILESYSTEM_ADAPTER,
        LLM_SERVICE,
        MEMORY_SELECTOR,
        PERSON_REPOSITORY,
        PROMPT_LOADING_SERVICE,
    )
    from dipeo.infrastructure.llm.domain_adapters import LLMMemorySelectionAdapter

    def create_execution_orchestrator() -> ExecutionOrchestrator:
        """Factory for execution orchestrator with all dependencies."""
        person_repo = registry.resolve(PERSON_REPOSITORY)
        manage_conversation_use_case = registry.resolve(MANAGE_CONVERSATION_USE_CASE)

        # Create PromptLoadingUseCase
        filesystem_adapter = registry.resolve(FILESYSTEM_ADAPTER)
        prompt_loading = PromptLoadingUseCase(filesystem_adapter)
        registry.register(PROMPT_LOADING_SERVICE, prompt_loading)

        # Get LLM service
        llm_service = registry.resolve(LLM_SERVICE)

        # Create orchestrator with all dependencies
        orchestrator = ExecutionOrchestrator(
            person_repository=person_repo,
            manage_conversation_use_case=manage_conversation_use_case,
            prompt_loading_use_case=prompt_loading,
            memory_selector=None,  # Will be set after creation
            llm_service=llm_service,
        )

        # Create LLMMemorySelectionAdapter with orchestrator
        memory_selector = LLMMemorySelectionAdapter(orchestrator)
        registry.register(MEMORY_SELECTOR, memory_selector)

        # Update orchestrator with memory_selector
        orchestrator._memory_selector = memory_selector

        return orchestrator

    registry.register(EXECUTION_ORCHESTRATOR, lambda: create_execution_orchestrator())

    # Wire execute diagram use case
    from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase

    def create_execute_diagram() -> ExecuteDiagramUseCase:
        """Factory for execute diagram use case."""
        # ExecuteDiagramUseCase has a different constructor signature
        return ExecuteDiagramUseCase(service_registry=registry)

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

    registry.register(PREPARE_DIAGRAM_USE_CASE, create_prepare_diagram)

    # Wire CLI session service
    from dipeo.application.execution.use_cases.cli_session import CliSessionService

    def create_cli_session_service() -> CliSessionService:
        """Factory for CLI session service."""
        return CliSessionService()

    registry.register(CLI_SESSION_USE_CASE, create_cli_session_service)
