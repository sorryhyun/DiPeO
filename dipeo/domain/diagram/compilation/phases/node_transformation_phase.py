"""Node transformation phase for diagram compilation."""

from dipeo.diagram_generated import NodeType

from ..node_factory import NodeFactory
from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class NodeTransformationPhase(PhaseInterface):
    """Phase 2: Transform domain nodes into typed executable nodes."""

    def __init__(self, node_factory: NodeFactory):
        self.node_factory = node_factory

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.NODE_TRANSFORMATION

    def execute(self, context: CompilationContext) -> None:
        """Transform nodes and build node map and metadata."""
        context.typed_nodes = self.node_factory.create_typed_nodes(context.nodes_list)

        for error in self.node_factory.get_validation_errors():
            context.result.add_error(self.phase_type, error)

        context.node_map = {node.id: node for node in context.typed_nodes}

        self._extract_metadata(context)

    def _extract_metadata(self, context: CompilationContext) -> None:
        """Extract start nodes and person nodes metadata."""
        for node in context.typed_nodes:
            if node.type == NodeType.START:
                context.start_nodes.add(node.id)
            elif node.type == NodeType.PERSON_JOB:
                person_id = getattr(node, "person_id", None)
                if person_id:
                    if person_id not in context.person_nodes:
                        context.person_nodes[person_id] = []
                    context.person_nodes[person_id].append(node.id)
