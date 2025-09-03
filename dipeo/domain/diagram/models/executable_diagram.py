"""ExecutableDiagram static object representing a resolved diagram ready for execution."""

from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated import ContentType
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Protocol
import warnings

@dataclass(frozen=True)
class BaseExecutableNode:
    id: NodeID
    type: NodeType
    position: Vec2
    label: str = ""
    flipped: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "type": self.type.value,
            "position": {"x": self.position.x, "y": self.position.y},
            "label": self.label,
            "flipped": self.flipped
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class ExecutableNode(Protocol):
    id: NodeID
    type: NodeType
    position: Vec2
    
    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ExecutableEdgeV2:
    """Enhanced edge representation with all resolution rules.
    
    This unified structure contains all information needed for both
    compile-time validation and runtime execution.
    """
    # Identity
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    
    # Connection details
    source_output: str = "default"
    target_input: str = "default"
    
    # Transformation rules (determined at compile time)
    content_type: ContentType | None = None
    transform_rules: dict[str, Any] = field(default_factory=dict)
    
    # Runtime behavior hints
    is_conditional: bool = False
    requires_first_execution: bool = False
    execution_priority: int = 0  # Higher priority edges execute first (default: 0)
    
    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def get_transform_rule(self, rule_type: str) -> Any | None:
        """Get a specific transformation rule."""
        return self.transform_rules.get(rule_type)
    
    def has_transform_rule(self, rule_type: str) -> bool:
        """Check if a transformation rule exists."""
        return rule_type in self.transform_rules
    
    def __repr__(self) -> str:
        return f"ExecutableEdgeV2({self.source_node_id} -> {self.target_node_id})"


class NodeOutputProtocolV2(Protocol):
    """Enhanced protocol for node outputs with consistent access patterns."""
    
    @property
    def value(self) -> Any:
        """Primary output value."""
        ...
    
    @property
    def outputs(self) -> dict[str, Any]:
        """Named outputs dictionary."""
        ...
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Output metadata."""
        ...
    
    def get_output(self, name: str = "default") -> Any:
        """Get a specific named output or default value."""
        ...
    
    def has_output(self, name: str) -> bool:
        """Check if a named output exists."""
        ...


@dataclass
class StandardNodeOutput:
    """Standard implementation of NodeOutputProtocolV2.
    
    DEPRECATED: This class is deprecated in favor of the Envelope pattern
    with multi-representation support. Use Envelope.with_representations()
    for new code. This class will be removed in future releases.
    
    Migration path:
    - For new handlers: Return Envelope directly from serialize_output()
    - For existing code: Continue using StandardNodeOutput with fallback support
    - See: /docs/migration/envelope_migration_guide.md for details
    """
    
    value: Any
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Issue deprecation warning on instantiation."""
        warnings.warn(
            "StandardNodeOutput is deprecated. Use Envelope with representations instead. "
            "See /docs/migration/envelope_migration_guide.md for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def get_output(self, name: str = "default") -> Any:
        """Get a specific named output or default value."""
        if name == "default":
            return self.outputs.get(name, self.value)
        return self.outputs.get(name)
    
    def has_output(self, name: str) -> bool:
        """Check if a named output exists."""
        if name == "default":
            return True  # Always has default
        return name in self.outputs
    
    @classmethod
    def from_value(cls, value: Any) -> "StandardNodeOutput":
        """Create from a simple value.
        
        DEPRECATED: Use EnvelopeFactory instead.
        """
        warnings.warn(
            "StandardNodeOutput.from_value() is deprecated. "
            "Use EnvelopeFactory.text() or EnvelopeFactory.json() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return cls(value=value, outputs={"default": value})
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StandardNodeOutput":
        """Create from a dictionary representation.
        
        DEPRECATED: Use EnvelopeFactory instead.
        """
        warnings.warn(
            "StandardNodeOutput.from_dict() is deprecated. "
            "Use EnvelopeFactory with representations instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if "value" in data:
            return cls(
                value=data["value"],
                outputs=data.get("outputs", {"default": data["value"]}),
                metadata=data.get("metadata", {})
            )
        else:
            # Treat entire dict as outputs
            return cls(
                value=data.get("default", data),
                outputs=data,
                metadata={}
            )


class ExecutableDiagram:
    """Resolved diagram ready for execution.
    
    Static object with resolved handles, executable edges,
    enriched nodes, and calculated execution order.
    """
    
    def __init__(self, 
                 nodes: list[ExecutableNode], 
                 edges: list[ExecutableEdgeV2],
                 execution_order: list[NodeID] | None = None,
                 metadata: dict[str, Any] | None = None,
                 api_keys: dict[str, str] | None = None):
        self.nodes: tuple[ExecutableNode, ...] = tuple(nodes)
        self.edges: tuple[ExecutableEdgeV2, ...] = tuple(edges)
        self.execution_order: tuple[NodeID, ...] = tuple(execution_order) if execution_order else tuple()
        self.metadata: dict[str, Any] = metadata or {}
        self.api_keys: dict[str, str] = api_keys or {}
        self._node_index: dict[NodeID, ExecutableNode] = {
            node.id: node for node in self.nodes
        }
        self._outgoing_edges: dict[NodeID, list[ExecutableEdgeV2]] = {}
        self._incoming_edges: dict[NodeID, list[ExecutableEdgeV2]] = {}
        for edge in self.edges:
            self._outgoing_edges.setdefault(edge.source_node_id, []).append(edge)
            self._incoming_edges.setdefault(edge.target_node_id, []).append(edge)
        
        self._start_nodes: list[NodeID] = []
        self._person_nodes: dict[NodeID, str] = {}
        self._node_dependencies: dict[NodeID, list[dict[str, str]]] = {}
        
        self._build_execution_hints()
    
    def _build_execution_hints(self) -> None:
        self._start_nodes = [node.id for node in self.nodes if node.type == NodeType.START]
        
        for node in self.nodes:
            if hasattr(node, 'type') and node.type == NodeType.PERSON_JOB:
                if hasattr(node, 'data') and isinstance(node.data, dict):
                    person_id = node.data.get('person_id') or node.data.get('personId')
                    if person_id:
                        self._person_nodes[node.id] = person_id
        for node_id in self._node_index:
            dependencies = []
            for edge in self.get_incoming_edges(node_id):
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
    
    def get_outgoing_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]:
        return self._outgoing_edges.get(node_id, [])
    
    def get_incoming_edges(self, node_id: NodeID) -> list[ExecutableEdgeV2]:
        return self._incoming_edges.get(node_id, [])
    
    def get_start_nodes(self) -> list[ExecutableNode]:
        return self.get_nodes_by_type(NodeType.START)
    
    
    def get_next_nodes(self, node_id: NodeID) -> list[ExecutableNode]:
        edges = self.get_outgoing_edges(node_id)
        return [self.get_node(edge.target_node_id) 
                for edge in edges 
                if self.get_node(edge.target_node_id) is not None]
    
    
    
    def get_execution_hints(self) -> dict[str, Any]:
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