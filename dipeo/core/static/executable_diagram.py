"""ExecutableDiagram static object representing a resolved diagram ready for execution."""

from typing import List, Optional, Tuple, Dict, Any, Protocol
from dataclasses import dataclass, field

from dipeo.models import NodeID, NodeType, Vec2


class ExecutableNode(Protocol):
    """Protocol for executable nodes with resolved configuration."""
    id: NodeID
    type: NodeType
    position: Vec2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        ...


@dataclass(frozen=True)
class ExecutableEdge:
    """Immutable edge representing a resolved connection with data flow.
    
    Unlike DomainArrows which use handles, ExecutableEdges have direct
    node ID references and resolved data transformation rules.
    """
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_output: Optional[str] = None
    target_input: Optional[str] = None
    data_transform: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        """String representation of the edge."""
        return f"ExecutableEdge({self.source_node_id} -> {self.target_node_id})"


class ExecutableDiagram:
    """Resolved diagram ready for execution.
    
    This is a static object representing a fully resolved diagram where:
    - All handle references have been resolved to concrete node IDs
    - Arrows have been transformed into executable edges with data flow
    - Nodes are enriched with runtime configuration
    - Execution order has been calculated and validated
    
    The diagram is immutable once created and represents the execution plan.
    """
    
    def __init__(self, 
                 nodes: List[ExecutableNode], 
                 edges: List[ExecutableEdge],
                 execution_order: List[NodeID],
                 metadata: Optional[Dict[str, Any]] = None,
                 api_keys: Optional[Dict[str, str]] = None):
        """Initialize an ExecutableDiagram.
        
        Args:
            nodes: List of resolved, validated nodes
            edges: List of resolved connections with data flow
            execution_order: Pre-calculated topological execution order
            metadata: Optional diagram metadata
            api_keys: Optional API keys needed for execution
        """
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
        """Build execution hints from the diagram structure."""
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
        """Get a node by its ID.
        
        Args:
            node_id: The ID of the node to retrieve
            
        Returns:
            The node if found, None otherwise
        """
        return self._node_index.get(node_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[ExecutableNode]:
        """Get all nodes of a specific type.
        
        Args:
            node_type: The type of nodes to retrieve
            
        Returns:
            List of nodes matching the specified type
        """
        return [node for node in self.nodes if node.type == node_type]
    
    def get_outgoing_edges(self, node_id: NodeID) -> List[ExecutableEdge]:
        """Get all edges originating from a node.
        
        Args:
            node_id: The ID of the source node
            
        Returns:
            List of edges from the specified node
        """
        return self._outgoing_edges.get(node_id, [])
    
    def get_incoming_edges(self, node_id: NodeID) -> List[ExecutableEdge]:
        """Get all edges targeting a node.
        
        Args:
            node_id: The ID of the target node
            
        Returns:
            List of edges to the specified node
        """
        return self._incoming_edges.get(node_id, [])
    
    def get_start_nodes(self) -> List[ExecutableNode]:
        """Get all start nodes in the diagram.
        
        Returns:
            List of nodes with type 'start'
        """
        return self.get_nodes_by_type(NodeType.start)
    
    def get_end_nodes(self) -> List[ExecutableNode]:
        """Get all endpoint nodes in the diagram.
        
        Returns:
            List of nodes with type 'endpoint'
        """
        return self.get_nodes_by_type(NodeType.endpoint)
    
    def get_next_nodes(self, node_id: NodeID) -> List[ExecutableNode]:
        """Get all nodes that follow a given node.
        
        Args:
            node_id: The ID of the current node
            
        Returns:
            List of nodes that are connected downstream
        """
        edges = self.get_outgoing_edges(node_id)
        return [self.get_node(edge.target_node_id) 
                for edge in edges 
                if self.get_node(edge.target_node_id) is not None]
    
    def get_previous_nodes(self, node_id: NodeID) -> List[ExecutableNode]:
        """Get all nodes that precede a given node.
        
        Args:
            node_id: The ID of the current node
            
        Returns:
            List of nodes that are connected upstream
        """
        edges = self.get_incoming_edges(node_id)
        return [self.get_node(edge.source_node_id) 
                for edge in edges 
                if self.get_node(edge.source_node_id) is not None]
    
    def validate(self) -> List[str]:
        """Validate the diagram structure.
        
        Returns:
            List of validation errors, empty if valid
        """
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
        """Get execution hints for the diagram.
        
        Returns:
            Dictionary containing:
            - start_nodes: List of start node IDs
            - person_nodes: Mapping of node_id to person_id
            - node_dependencies: Mapping of node_id to dependency list
        """
        return {
            "start_nodes": self._start_nodes,
            "person_nodes": self._person_nodes,
            "node_dependencies": self._node_dependencies
        }
    
    def get_person_id_for_node(self, node_id: NodeID) -> Optional[str]:
        """Get the person ID associated with a node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The person ID if the node is a person job node, None otherwise
        """
        return self._person_nodes.get(node_id)
    
    def get_node_dependencies(self, node_id: NodeID) -> List[Dict[str, str]]:
        """Get the dependencies for a node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            List of dependency dictionaries with 'source' and 'variable' keys
        """
        return self._node_dependencies.get(node_id, [])
    
    def __repr__(self) -> str:
        """String representation of the ExecutableDiagram."""
        return (f"ExecutableDiagram(nodes={len(self.nodes)}, "
                f"edges={len(self.edges)}, "
                f"execution_order={len(self.execution_order)} nodes)")