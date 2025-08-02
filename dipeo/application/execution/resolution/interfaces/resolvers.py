"""Interface definitions for compile-time and runtime resolvers.

These interfaces define the clear boundaries between static analysis 
at compile time and dynamic resolution at runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from dipeo.core.static.executable_diagram import ExecutableEdge, ExecutableNode
from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID


class Connection:
    """Represents a resolved connection between nodes."""
    
    def __init__(
        self,
        source_node_id: NodeID,
        target_node_id: NodeID,
        source_output: str | None = None,
        target_input: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.source_output = source_output
        self.target_input = target_input
        self.metadata = metadata or {}


class TransformRules:
    """Encapsulates transformation rules for a connection."""
    
    def __init__(self, rules: dict[str, Any] | None = None):
        self.rules = rules or {}
    
    def add_rule(self, rule_type: str, config: Any) -> None:
        self.rules[rule_type] = config
    
    def get_rule(self, rule_type: str) -> Any | None:
        return self.rules.get(rule_type)
    
    def merge_with(self, other: "TransformRules") -> "TransformRules":
        """Merge with another set of rules, other takes precedence."""
        merged = TransformRules(self.rules.copy())
        merged.rules.update(other.rules)
        return merged
    
    def __iter__(self):
        return iter(self.rules.items())


class CompileTimeResolver(ABC):
    """Resolves static structure and transformation rules at compile time."""
    
    @abstractmethod
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes.
        
        This includes:
        - Handle resolution
        - Connection validation
        - Special input detection (like "first" inputs)
        """
        pass
    
    @abstractmethod
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> TransformRules:
        """Determine all transformation rules for a connection.
        
        This includes:
        - Content type determination
        - Transformation rule extraction from arrows
        - Node type specific rules
        """
        pass
    
    @abstractmethod
    def validate_connection(
        self,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> tuple[bool, str | None]:
        """Validate if a connection is allowed between node types.
        
        Returns (is_valid, error_message).
        """
        pass


class ExecutionContext(Protocol):
    """Protocol for execution context needed by runtime resolver."""
    
    @property
    def node_exec_counts(self) -> dict[str, int]:
        """Get execution counts for nodes."""
        ...
    
    @property
    def is_first_execution(self) -> bool:
        """Check if this is the first execution."""
        ...
    
    def get_node_output(self, node_id: str) -> Any:
        """Get output value for a node."""
        ...


class RuntimeInputResolver(ABC):
    """Resolves actual input values during execution."""
    
    @abstractmethod
    def resolve_inputs(
        self,
        node_id: str,
        edges: list[ExecutableEdge],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve runtime input values for a node.
        
        This includes:
        - Getting actual values from source nodes
        - Applying transformations
        - Handling conditional edges
        """
        pass
    
    @abstractmethod
    def should_process_edge(
        self,
        edge: ExecutableEdge,
        node: ExecutableNode,
        context: ExecutionContext
    ) -> bool:
        """Determine if an edge should be processed in current execution state."""
        pass
    
    @abstractmethod
    def get_edge_value(
        self,
        edge: ExecutableEdge,
        context: ExecutionContext
    ) -> Any:
        """Extract the actual value from an edge's source node."""
        pass
    
    @abstractmethod
    def apply_transformations(
        self,
        value: Any,
        edge: ExecutableEdge
    ) -> Any:
        """Apply transformation rules to a value."""
        pass