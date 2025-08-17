"""Domain-owned input resolution interfaces.

This module provides the domain contracts for compile-time and runtime
input resolution, enabling clean separation between static analysis and dynamic execution.
Moved from core/resolution to establish domain ownership.
"""

from typing import Any, Protocol
from abc import ABC, abstractmethod
from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID
from dipeo.diagram_generated.enums import NodeType


# ============================================================================
# Data Structures
# ============================================================================

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


# ============================================================================
# Compile-Time Resolution
# ============================================================================

class CompileTimeResolver(ABC):
    """Base class for resolving static structure and transformation rules at compile time.
    
    This resolver works during diagram compilation to determine connections
    and transformation rules that will be used during execution.
    """
    
    @abstractmethod
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes.
        
        Args:
            arrows: List of domain arrows defining connections
            nodes: List of domain nodes in the diagram
            
        Returns:
            List of resolved connections with source/target information
        """
        pass
    
    @abstractmethod
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node_type: NodeType,
        target_node_type: NodeType,
        nodes_by_id: dict[NodeID, DomainNode]
    ) -> TransformRules:
        """Determine all transformation rules for a connection.
        
        Args:
            connection: The resolved connection
            source_node_type: Type of the source node
            target_node_type: Type of the target node
            nodes_by_id: Mapping of node IDs to nodes
            
        Returns:
            Transformation rules to apply for this connection
        """
        pass


# ============================================================================
# Runtime Resolution
# ============================================================================

class RuntimeInputResolver(ABC):
    """Base class for resolving actual input values at runtime.
    
    This resolver works during diagram execution to provide actual values
    for node inputs based on outputs from previously executed nodes.
    """
    
    @abstractmethod
    async def resolve_input_value(
        self,
        target_node_id: NodeID,
        target_input: str,
        node_outputs: dict[NodeID, Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve the actual value for a node's input at runtime.
        
        Args:
            target_node_id: ID of the node needing input
            target_input: Name of the input to resolve
            node_outputs: Outputs from previously executed nodes
            transformation_rules: Optional transformation rules to apply
            
        Returns:
            The resolved input value
        """
        pass


# ============================================================================
# Transformation Engine
# ============================================================================

class TransformationEngine(ABC):
    """Base class for applying data transformations based on content types.
    
    This engine applies transformation rules determined at compile-time
    to values during runtime execution.
    """
    
    @abstractmethod
    def transform(
        self,
        value: Any,
        rules: TransformRules,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value.
        
        Args:
            value: The value to transform
            rules: Transformation rules to apply
            source_content_type: Optional source content type
            target_content_type: Optional target content type
            
        Returns:
            The transformed value
        """
        pass


# ============================================================================
# Protocol Versions for V2 System
# ============================================================================

class CompileTimeResolverV2(Protocol):
    """Protocol version of CompileTimeResolver for V2 system."""
    
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes."""
        ...
    
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node_type: NodeType,
        target_node_type: NodeType,
        nodes_by_id: dict[NodeID, DomainNode]
    ) -> TransformRules:
        """Determine all transformation rules for a connection."""
        ...


class RuntimeInputResolverV2(Protocol):
    """Protocol version of RuntimeInputResolver for V2 system."""
    
    async def resolve_input_value(
        self,
        target_node_id: NodeID,
        target_input: str,
        node_outputs: dict[NodeID, Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve the actual value for a node's input at runtime."""
        ...


class TransformationEngineV2(Protocol):
    """Protocol version of TransformationEngine for V2 system."""
    
    def transform(
        self,
        value: Any,
        rules: TransformRules,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value."""
        ...