"""Protocol for diagram queries that ExecutableDiagram already implements."""

from typing import Any, Protocol

from dipeo.diagram_generated.domain_models import NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode


class DiagramQueryPort(Protocol):
    def get_node(self, node_id: NodeID) -> ExecutableNode | None: ...

    def get_nodes_by_type(self, node_type: Any) -> list[ExecutableNode]: ...

    def get_incoming_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]: ...

    def get_outgoing_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]: ...

    def get_start_nodes(self) -> list[ExecutableNode]: ...
