"""Simplified input resolution strategies for NodeView.

This module provides a cleaner approach to input resolution using
strategy patterns instead of complex nested conditionals.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from dipeo.domain.models import HandleLabel, ContentType, NodeType


class InputResolver(Protocol):
    """Protocol for input resolution strategies."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        """Check if this resolver can handle the given edge."""
        ...
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        """Resolve the input value for the edge."""
        ...


@dataclass
class ConditionNodeResolver:
    """Resolver for inputs from condition nodes."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return edge.source_view.node.type == NodeType.condition.value
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        # Use source handle to select the appropriate branch
        source_handle = edge.source_handle
        return source_values.get(source_handle)


@dataclass
class ConversationStateResolver:
    """Resolver for conversation state edges."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return (
            edge.content_type == ContentType.conversation_state.value 
            and "conversation" in source_values
        )
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get("conversation")


@dataclass
class ExactMatchResolver:
    """Resolver for exact label matches."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return edge.label in source_values
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get(edge.label)


@dataclass
class DefaultValueResolver:
    """Resolver for default handle values."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return HandleLabel.default.value in source_values
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get(HandleLabel.default.value)


@dataclass
class ConversationFallbackResolver:
    """Resolver for conversation fallback."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return "conversation" in source_values
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get("conversation")


@dataclass
class SingleValueResolver:
    """Resolver for single value outputs."""
    
    def can_resolve(self, edge: Any, source_values: Dict[str, Any]) -> bool:
        return len(source_values) == 1
    
    def resolve(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return list(source_values.values())[0] if source_values else None


class InputResolutionStrategy:
    """Main strategy for resolving inputs with prioritized resolvers."""
    
    def __init__(self):
        # Ordered list of resolvers (priority matters)
        self.resolvers = [
            ConditionNodeResolver(),
            ConversationStateResolver(),
            ExactMatchResolver(),
            DefaultValueResolver(),
            ConversationFallbackResolver(),
            SingleValueResolver(),
        ]
    
    def resolve_input(self, edge: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        """Resolve input value using the first applicable resolver."""
        for resolver in self.resolvers:
            if resolver.can_resolve(edge, source_values):
                return resolver.resolve(edge, source_values)
        return None
    
    def should_process_edge(self, edge: Any, node_type: str, exec_count: int) -> bool:
        """Determine if an edge should be processed based on node type and execution count."""
        # Skip edges with no output
        if edge.source_view.output is None:
            return False
        
        # Handle person_job first edge logic
        if node_type == NodeType.person_job.value:
            is_first_edge = edge.target_handle == "first"
            is_first_execution = exec_count == 0
            
            # Process first edges only on first execution
            if is_first_edge:
                return is_first_execution
            # Process non-first edges on all executions except first
            else:
                return True
        
        # For all other node types, process all edges
        return True
    
    def should_skip_condition_branch(self, edge: Any) -> bool:
        """Check if condition branch should be skipped."""
        if edge.source_view.node.type != NodeType.condition.value:
            return False
            
        condition_result = edge.source_view.output.metadata.get("condition_result", False)
        edge_branch = edge.arrow.data.get("branch") if edge.arrow.data else None
        
        # If branch data exists in arrow data, use it
        if edge_branch is not None:
            edge_branch_bool = edge_branch.lower() == "true"
            return edge_branch_bool != condition_result
        
        # Otherwise, check the source handle for condtrue/condfalse
        source_handle = edge.source_handle
        if source_handle in ["condtrue", "condfalse"]:
            edge_branch_bool = source_handle == "condtrue"
            return edge_branch_bool != condition_result
            
        # If no branch info found, don't skip
        return False


def get_active_inputs_simplified(node_view: Any) -> Dict[str, Any]:
    """Simplified version of get_active_inputs using the strategy pattern."""
    strategy = InputResolutionStrategy()
    inputs = {}
    
    # Process each incoming edge
    for edge in node_view.incoming_edges:
        # Check if edge should be processed
        if not strategy.should_process_edge(edge, node_view.node.type, node_view.exec_count):
            continue
        
        # Skip wrong condition branches
        if strategy.should_skip_condition_branch(edge):
            continue
        
        # Get source values
        source_values = edge.source_view.output.value
        if not isinstance(source_values, dict):
            continue
        
        # Resolve value using strategy
        value = strategy.resolve_input(edge, source_values)
        if value is not None:
            inputs[edge.label] = value
    
    return inputs