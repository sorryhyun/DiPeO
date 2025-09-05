"""Protocol for diagram queries that ExecutableDiagram already implements."""

from typing import Any, Protocol

from dipeo.diagram_generated.domain_models import NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode


class DiagramQueryPort(Protocol):
    """Protocol for diagram queries that ExecutableDiagram already implements."""

    def get_node(self, node_id: NodeID) -> ExecutableNode | None:
        """Get a node by its ID."""
        ...

    def get_nodes_by_type(self, node_type: Any) -> list[ExecutableNode]:
        """Get all nodes of a specific type."""
        ...

    def get_incoming_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]:
        """Get all edges that target the specified node."""
        ...

    def get_outgoing_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]:
        """Get all edges that originate from the specified node."""
        ...

    def get_start_nodes(self) -> list[ExecutableNode]:
        """Get all start nodes in the diagram."""
        ...
