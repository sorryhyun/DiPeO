"""CLI session mutations for GraphQL schema."""

import strawberry
from typing import Optional
import logging

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.application.services.cli_session_service import CliSessionService
from ...types.inputs import RegisterCliSessionInput, UnregisterCliSessionInput
from ...types.results import CliSessionResult

logger = logging.getLogger(__name__)

# Service key for CLI session service
CLI_SESSION_SERVICE = ServiceKey[CliSessionService]("cli_session_service")


def create_cli_session_mutations(registry: UnifiedServiceRegistry) -> type:
    """Create CLI session mutation methods with injected service registry."""
    
    @strawberry.type
    class CliSessionMutations:
        @strawberry.mutation
        async def register_cli_session(self, input: RegisterCliSessionInput) -> CliSessionResult:
            """Register a new CLI execution session."""
            try:
                # Get or create CLI session service
                cli_session_service = registry.get(CLI_SESSION_SERVICE.name)
                if not cli_session_service:
                    cli_session_service = CliSessionService()
                    registry.register(CLI_SESSION_SERVICE.name, cli_session_service)
                
                # Register the session
                session = await cli_session_service.start_cli_session(
                    execution_id=input.execution_id,
                    diagram_name=input.diagram_name,
                    diagram_format=input.diagram_format,
                    diagram_data=input.diagram_data
                )
                
                return CliSessionResult(
                    success=True,
                    message=f"CLI session registered for execution {input.execution_id}"
                )
                
            except Exception as e:
                logger.error(f"Failed to register CLI session: {e}")
                return CliSessionResult(
                    success=False,
                    error=f"Failed to register CLI session: {str(e)}"
                )
        
        @strawberry.mutation
        async def unregister_cli_session(self, input: UnregisterCliSessionInput) -> CliSessionResult:
            """Unregister a CLI execution session."""
            try:
                cli_session_service = registry.get(CLI_SESSION_SERVICE.name)
                if not cli_session_service:
                    return CliSessionResult(
                        success=False,
                        error="CLI session service not available"
                    )
                
                # Unregister the session
                success = await cli_session_service.end_cli_session(input.execution_id)
                
                if success:
                    return CliSessionResult(
                        success=True,
                        message=f"CLI session unregistered for execution {input.execution_id}"
                    )
                else:
                    return CliSessionResult(
                        success=False,
                        error=f"No active CLI session found for execution {input.execution_id}"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to unregister CLI session: {e}")
                return CliSessionResult(
                    success=False,
                    error=f"Failed to unregister CLI session: {str(e)}"
                )
    
    return CliSessionMutations