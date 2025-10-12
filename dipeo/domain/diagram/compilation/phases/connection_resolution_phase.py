"""Connection resolution phase for diagram compilation."""

from ..connection_resolver import ConnectionResolver
from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class ConnectionResolutionPhase(PhaseInterface):
    """Phase 3: Resolve handle references to actual node connections."""

    def __init__(self, connection_resolver: ConnectionResolver):
        self.connection_resolver = connection_resolver

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.CONNECTION_RESOLUTION

    def execute(self, context: CompilationContext) -> None:
        """Resolve connections from arrows to node handles."""
        resolved, errors = self.connection_resolver.resolve_connections(
            context.arrows_list, context.nodes_list
        )

        context.resolved_connections = resolved

        for error in errors:
            context.result.add_error(self.phase_type, error)
