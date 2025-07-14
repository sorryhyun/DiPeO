"""ExecutableDiagram static object representing a resolved diagram ready for execution."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from dipeo.models import NodeID, NodeType, Vec2


class ExecutableNode(Protocol):
    id: NodeID
    type: NodeType
    position: Vec2
    
    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ExecutableEdge:
    """Immutable edge with resolved connection and data flow.
    
    Has direct node ID references and data transformation rules.
    """
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_output: str | None = None
    target_input: str | None = None
    data_transform: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"ExecutableEdge({self.source_node_id} -> {self.target_node_id})"


class ExecutableDiagram:
    """Resolved diagram ready for execution.
    
    Static object with resolved handles, executable edges,
    enriched nodes, and calculated execution order.
    """
    
    def __init__(self, 
                 nodes: list[ExecutableNode], 
                 edges: list[ExecutableEdge],
                 execution_order: list[NodeID],
                 metadata: dict[str, Any] | None = None,
                 api_keys: dict[str, str] | None = None):
        # Make immutable by converting to tuples
        self.nodes: tuple[ExecutableNode, ...] = tuple(nodes)
        self.edges: tuple[ExecutableEdge, ...] = tuple(edges)
        self.execution_order: tuple[NodeID, ...] = tuple(execution_order)
        self.metadata: dict[str, Any] = metadata or {}
        self.api_keys: dict[str, str] = api_keys or {}
        
        # Create lookup indices for efficient access
        self._node_index: dict[NodeID, ExecutableNode] = {
            node.id: node for node in self.nodes
        }
        self._outgoing_edges: dict[NodeID, list[ExecutableEdge]] = {}
        self._incoming_edges: dict[NodeID, list[ExecutableEdge]] = {}
        
        # Build edge indices
        for edge in self.edges:
            self._outgoing_edges.setdefault(edge.source_node_id, []).append(edge)
            self._incoming_edges.setdefault(edge.target_node_id, []).append(edge)
        
        # Execution hints cache
        self._start_nodes: list[NodeID] = []
        self._person_nodes: dict[NodeID, str] = {}  # node_id -> person_id
        self._node_dependencies: dict[NodeID, list[dict[str, str]]] = {}  # node_id -> [{"source": node_id, "variable": name}]
        
        # Build execution hints
        self._build_execution_hints()
    
    def _build_execution_hints(self) -> None:
        # Find start nodes
        self._start_nodes = [node.id for node in self.nodes if node.type == NodeType.start]
        
        # Find person nodes and their person IDs
        for node in self.nodes:
            if hasattr(node, 'type') and node.type == NodeType.person_job:
                # Get person_id from node data if available
                if hasattr(node, 'data') and isinstance(node.data, dict):
                    person_id = node.data.get('person_id') or node.data.get('personId')
                    if person_id:
                        self._person_nodes[node.id] = person_id
        
        # Build node dependencies from edges
        for node_id in self._node_index:
            dependencies = []
            for edge in self.get_incoming_edges(node_id):
                # Extract variable name from edge metadata or use default
                variable = "flow"
                if edge.source_output:
                    variable = edge.source_output
                elif edge.metadata and edge.metadata.get("label"):
                    variable = edge.metadata["label"]
                
                dependencies.append({
                    "source": edge.source_node_id,
                    "variable": variable
                })
            
            if dependencies:
                self._node_dependencies[node_id] = dependencies
    
    def get_node(self, node_id: NodeID) -> ExecutableNode | None:
        return self._node_index.get(node_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> list[ExecutableNode]:
        return [node for node in self.nodes if node.type == node_type]
    
    def get_outgoing_edges(self, node_id: NodeID) -> list[ExecutableEdge]:
        return self._outgoing_edges.get(node_id, [])
    
    def get_incoming_edges(self, node_id: NodeID) -> list[ExecutableEdge]:
        return self._incoming_edges.get(node_id, [])
    
    def get_start_nodes(self) -> list[ExecutableNode]:
        return self.get_nodes_by_type(NodeType.start)
    
    
    def get_next_nodes(self, node_id: NodeID) -> list[ExecutableNode]:
        edges = self.get_outgoing_edges(node_id)
        return [self.get_node(edge.target_node_id) 
                for edge in edges 
                if self.get_node(edge.target_node_id) is not None]
    
    
    
    def get_execution_hints(self) -> dict[str, Any]:
        """Get execution hints with start nodes, person nodes, and dependencies."""
        return {
            "start_nodes": self._start_nodes,
            "person_nodes": self._person_nodes,
            "node_dependencies": self._node_dependencies
        }
    
    def get_person_id_for_node(self, node_id: NodeID) -> str | None:
        return self._person_nodes.get(node_id)
    
    def get_node_dependencies(self, node_id: NodeID) -> list[dict[str, str]]:
        return self._node_dependencies.get(node_id, [])
    
    def __repr__(self) -> str:
        return (f"ExecutableDiagram(nodes={len(self.nodes)}, "
                f"edges={len(self.edges)}, "
                f"execution_order={len(self.execution_order)} nodes)")