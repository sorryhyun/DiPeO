"""Wiring module for execution bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import EXECUTION_ORCHESTRATOR

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import ExecutionOrchestrator
    from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
    from dipeo.application.execution.use_cases.prepare_diagram import PrepareDiagramForExecutionUseCase
    from dipeo.application.execution.use_cases.cli_session import CliSessionService

logger = logging.getLogger(__name__)

# Define service keys for execution context
EXECUTE_DIAGRAM_USE_CASE = ServiceKey["ExecuteDiagramUseCase"]("execution.use_case.execute_diagram")
PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"]("execution.use_case.prepare_diagram")
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
    import dipeo.application.execution.handlers  # noqa: F401
    
    # Wire execution orchestrator
    from dipeo.application.execution.orchestrators.execution_orchestrator import ExecutionOrchestrator
    from dipeo.application.registry.keys import (
        CONVERSATION_REPOSITORY,
        PERSON_REPOSITORY,
    )
    
    def create_execution_orchestrator() -> ExecutionOrchestrator:
        """Factory for execution orchestrator."""
        person_repo = registry.resolve(PERSON_REPOSITORY)
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY)
        return ExecutionOrchestrator(
            person_repository=person_repo,
            conversation_repository=conversation_repo
        )
    
    registry.register(EXECUTION_ORCHESTRATOR, create_execution_orchestrator)
    
    # Wire execute diagram use case
    from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
    
    def create_execute_diagram() -> ExecuteDiagramUseCase:
        """Factory for execute diagram use case."""
        # ExecuteDiagramUseCase has a different constructor signature
        return ExecuteDiagramUseCase(service_registry=registry)
    
    registry.register(EXECUTE_DIAGRAM_USE_CASE, create_execute_diagram)
    
    # Wire prepare diagram use case
    from dipeo.application.execution.use_cases.prepare_diagram import PrepareDiagramForExecutionUseCase
    
    def create_prepare_diagram() -> PrepareDiagramForExecutionUseCase:
        """Factory for prepare diagram use case."""
        # PrepareDiagramForExecutionUseCase also uses service_registry
        return PrepareDiagramForExecutionUseCase(service_registry=registry)
    
    registry.register(PREPARE_DIAGRAM_USE_CASE, create_prepare_diagram)
    
    # Wire CLI session service
    from dipeo.application.execution.use_cases.cli_session import CliSessionService
    
    def create_cli_session_service() -> CliSessionService:
        """Factory for CLI session service."""
        return CliSessionService()
    
    registry.register(CLI_SESSION_USE_CASE, create_cli_session_service)
