"""CLI session query resolvers."""

from dipeo.application.execution.use_cases import CliSessionService
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import CLI_SESSION_SERVICE


async def get_active_cli_session(registry: ServiceRegistry) -> dict:
    """Get the active CLI session if any."""
    cli_session_service = registry.resolve(CLI_SESSION_SERVICE)
    if not cli_session_service:
        return {}

    if isinstance(cli_session_service, CliSessionService):
        session_data = await cli_session_service.get_active_session()
        if session_data:
            return {
                "execution_id": session_data.execution_id,
                "diagram_name": session_data.diagram_name,
                "diagram_format": session_data.diagram_format,
                "started_at": session_data.started_at.isoformat()
                if session_data.started_at
                else None,
                "is_active": session_data.is_active,
                "diagram_data": session_data.diagram_data,
                "node_states": session_data.node_states,
                "session_id": f"cli_{session_data.execution_id}",
            }

    return {}
