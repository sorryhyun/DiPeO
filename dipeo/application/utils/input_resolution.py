"""Simplified input resolution strategies for NodeView.

This module provides a cleaner approach to input resolution using
strategy patterns instead of complex nested conditionals.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from dipeo.models import NodeType
from dipeo.models import HandleLabel, ContentType


class InputResolver(Protocol):
    """Protocol for input resolution strategies."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        """Check if this resolver can handle the given arrow."""
        ...
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        """Resolve the input value for the arrow."""
        ...


@dataclass
class ConditionNodeResolver:
    """Resolver for inputs from condition nodes."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return arrow.source_view.node.type == NodeType.condition.value
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        # Use source handle to select the appropriate branch
        source_handle = arrow.source_handle
        return source_values.get(source_handle)


@dataclass
class ConversationStateResolver:
    """Resolver for conversation state arrows."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return (
            arrow.content_type == ContentType.conversation_state.value 
            and "conversation" in source_values
        )
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get("conversation")


@dataclass
class ExactMatchResolver:
    """Resolver for exact label matches."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return arrow.label in source_values
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get(arrow.label)


@dataclass
class DefaultValueResolver:
    """Resolver for default handle values."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return HandleLabel.default.value in source_values
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get(HandleLabel.default.value)


@dataclass
class ConversationFallbackResolver:
    """Resolver for conversation fallback."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return "conversation" in source_values
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        return source_values.get("conversation")


@dataclass
class SingleValueResolver:
    """Resolver for single value outputs."""
    
    def can_resolve(self, arrow: Any, source_values: Dict[str, Any]) -> bool:
        return len(source_values) == 1
    
    def resolve(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
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
    
    def resolve_input(self, arrow: Any, source_values: Dict[str, Any]) -> Optional[Any]:
        """Resolve input value using the first applicable resolver."""
        for resolver in self.resolvers:
            if resolver.can_resolve(arrow, source_values):
                return resolver.resolve(arrow, source_values)
        return None
    
    def should_process_arrow(self, arrow: Any, node_type: str, exec_count: int) -> bool:
        """Determine if an arrow should be processed based on node type and execution count."""
        # Skip arrows with no output
        if arrow.source_view.output is None:
            return False
        
        # Handle person_job first arrow logic
        if node_type == NodeType.person_job.value:
            is_first_arrow = arrow.target_handle == "first"
            is_first_execution = exec_count == 0
            
            # Process first arrows only on first execution
            if is_first_arrow:
                return is_first_execution
            # Process non-first arrows on all executions except first
            else:
                return True
        
        # For all other node types, process all arrows
        return True
    
    def should_skip_condition_branch(self, arrow: Any) -> bool:
        """Check if condition branch should be skipped."""
        if arrow.source_view.node.type != NodeType.condition.value:
            return False
            
        condition_result = arrow.source_view.output.metadata.get("condition_result", False)
        arrow_branch = arrow.arrow.data.get("branch") if arrow.arrow.data else None
        
        # If branch data exists in arrow data, use it
        if arrow_branch is not None:
            arrow_branch_bool = arrow_branch.lower() == "true"
            return arrow_branch_bool != condition_result
        
        # Otherwise, check the source handle for condtrue/condfalse
        source_handle = arrow.source_handle
        if source_handle in ["condtrue", "condfalse"]:
            arrow_branch_bool = source_handle == "condtrue"
            return arrow_branch_bool != condition_result
            
        # If no branch info found, don't skip
        return False


def get_active_inputs_simplified(node_view: Any) -> Dict[str, Any]:
    """Simplified version of get_active_inputs using the strategy pattern."""
    strategy = InputResolutionStrategy()
    inputs = {}
    
    # Process each incoming arrow
    for arrow in node_view.incoming_edges:
        # Check if arrow should be processed
        if not strategy.should_process_arrow(arrow, node_view.node.type, node_view.exec_count):
            continue
        
        # Skip wrong condition branches
        if strategy.should_skip_condition_branch(arrow):
            continue
        
        # Get source values
        source_values = arrow.source_view.output.value
        if not isinstance(source_values, dict):
            continue
        
        # Resolve value using strategy
        value = strategy.resolve_input(arrow, source_values)
        if value is not None:
            inputs[arrow.label] = value
    
    return inputs