"""Edge building phase for diagram compilation."""

from ..edge_builder import EdgeBuilder
from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class EdgeBuildingPhase(PhaseInterface):
    """Phase 4: Create executable edges with transformation rules."""

    def __init__(self, edge_builder: EdgeBuilder):
        self.edge_builder = edge_builder

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.EDGE_BUILDING

    def execute(self, context: CompilationContext) -> None:
        """Build executable edges and track dependencies."""
        edges, errors = self.edge_builder.build_edges(
            context.arrows_list, context.resolved_connections, context.node_map
        )

        context.typed_edges = edges

        for error in errors:
            context.result.add_error(self.phase_type, error)

        self._build_dependency_graph(context)

    def _build_dependency_graph(self, context: CompilationContext) -> None:
        """Build node dependency graph from edges."""
        for edge in context.typed_edges:
            if edge.target_node_id not in context.node_dependencies:
                context.node_dependencies[edge.target_node_id] = set()
            context.node_dependencies[edge.target_node_id].add(edge.source_node_id)
