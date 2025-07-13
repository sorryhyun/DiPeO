"""ExecutableDiagram static object representing a resolved diagram ready for execution."""

from typing import List, Optional, Tuple, Dict, Any, Protocol
from dataclasses import dataclass, field

from dipeo.models import NodeID, NodeType, Vec2


class ExecutableNode(Protocol):
    id: NodeID
    type: NodeType
    position: Vec2
    
    def to_dict(self) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class ExecutableEdge:
    """Immutable edge with resolved connection and data flow.
    
    Has direct node ID references and data transformation rules.
    """
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_output: Optional[str] = None
    target_input: Optional[str] = None
    data_transform: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"ExecutableEdge({self.source_node_id} -> {self.target_node_id})"


class ExecutableDiagram:
    """Resolved diagram ready for execution.
    
    Static object with resolved handles, executable edges,
    enriched nodes, and calculated execution order.
    """
    
    def __init__(self, 
                 nodes: List[ExecutableNode], 
                 edges: List[ExecutableEdge],
                 execution_order: List[NodeID],
                 metadata: Optional[Dict[str, Any]] = None,
                 api_keys: Optional[Dict[str, str]] = None):
        # Make immutable by converting to tuples
        self.nodes: Tuple[ExecutableNode, ...] = tuple(nodes)
        self.edges: Tuple[ExecutableEdge, ...] = tuple(edges)
        self.execution_order: Tuple[NodeID, ...] = tuple(execution_order)
        self.metadata: Dict[str, Any] = metadata or {}
        self.api_keys: Dict[str, str] = api_keys or {}
        
        # Create lookup indices for efficient access
        self._node_index: Dict[NodeID, ExecutableNode] = {
            node.id: node for node in self.nodes
        }
        self._outgoing_edges: Dict[NodeID, List[ExecutableEdge]] = {}
        self._incoming_edges: Dict[NodeID, List[ExecutableEdge]] = {}
        
        # Build edge indices
        for edge in self.edges:
            self._outgoing_edges.setdefault(edge.source_node_id, []).append(edge)
            self._incoming_edges.setdefault(edge.target_node_id, []).append(edge)
        
        # Execution hints cache
        self._start_nodes: List[NodeID] = []
        self._person_nodes: Dict[NodeID, str] = {}  # node_id -> person_id
        self._node_dependencies: Dict[NodeID, List[Dict[str, str]]] = {}  # node_id -> [{"source": node_id, "variable": name}]
        
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
    
    def get_node(self, node_id: NodeID) -> Optional[ExecutableNode]:
        return self._node_index.get(node_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[ExecutableNode]:
        return [node for node in self.nodes if node.type == node_type]
    
    def get_outgoing_edges(self, node_id: NodeID) -> List[ExecutableEdge]:
        return self._outgoing_edges.get(node_id, [])
    
    def get_incoming_edges(self, node_id: NodeID) -> List[ExecutableEdge]:
        return self._incoming_edges.get(node_id, [])
    
    def get_start_nodes(self) -> List[ExecutableNode]:
        return self.get_nodes_by_type(NodeType.start)
    
    def get_end_nodes(self) -> List[ExecutableNode]:
        return self.get_nodes_by_type(NodeType.endpoint)
    
    def get_next_nodes(self, node_id: NodeID) -> List[ExecutableNode]:
        edges = self.get_outgoing_edges(node_id)
        return [self.get_node(edge.target_node_id) 
                for edge in edges 
                if self.get_node(edge.target_node_id) is not None]
    
    def get_previous_nodes(self, node_id: NodeID) -> List[ExecutableNode]:
        edges = self.get_incoming_edges(node_id)
        return [self.get_node(edge.source_node_id) 
                for edge in edges 
                if self.get_node(edge.source_node_id) is not None]
    
    def validate(self) -> List[str]:
        errors = []
        
        # Check for at least one start node
        if not self.get_start_nodes():
            errors.append("Diagram must have at least one start node")
        
        # Check execution order includes all nodes
        order_set = set(self.execution_order)
        node_ids = {node.id for node in self.nodes}
        
        if order_set != node_ids:
            missing = node_ids - order_set
            extra = order_set - node_ids
            if missing:
                errors.append(f"Nodes missing from execution order: {missing}")
            if extra:
                errors.append(f"Unknown nodes in execution order: {extra}")
        
        # Check all edges reference valid nodes
        for edge in self.edges:
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge {edge.id} references unknown source: {edge.source_node_id}")
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge {edge.id} references unknown target: {edge.target_node_id}")
        
        return errors
    
    def get_execution_hints(self) -> Dict[str, Any]:
        """Get execution hints with start nodes, person nodes, and dependencies."""
        return {
            "start_nodes": self._start_nodes,
            "person_nodes": self._person_nodes,
            "node_dependencies": self._node_dependencies
        }
    
    def get_person_id_for_node(self, node_id: NodeID) -> Optional[str]:
        return self._person_nodes.get(node_id)
    
    def get_node_dependencies(self, node_id: NodeID) -> List[Dict[str, str]]:
        return self._node_dependencies.get(node_id, [])
    
    def __repr__(self) -> str:
        return (f"ExecutableDiagram(nodes={len(self.nodes)}, "
                f"edges={len(self.edges)}, "
                f"execution_order={len(self.execution_order)} nodes)")