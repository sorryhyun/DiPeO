"""Simplified node strategy implementations for input resolution."""

from typing import Any
from dipeo.diagram_generated import NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode
from dipeo.domain.execution.execution_context import ExecutionContext


class NodeStrategy:
    """Base strategy for node-type-specific behavior."""
    
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: ExecutionContext,
        has_special_inputs: bool = False
    ) -> bool:
        """Determine if an edge should be processed in current execution state.
        
        Default implementation processes all edges.
        """
        return True
    
    def transform_input(
        self,
        value: Any,
        edge: ExecutableEdgeV2,
        execution_context: ExecutionContext
    ) -> Any:
        """Apply node-type-specific transformations to input value.
        
        Default implementation returns value unchanged.
        """
        return value
    
    def has_first_inputs(self, incoming_edges: list[ExecutableEdgeV2]) -> bool:
        """Check if node has special 'first' inputs.
        
        Default implementation returns False.
        """
        return False


class PersonJobStrategy(NodeStrategy):
    """Strategy for PersonJob nodes with special 'first' input handling."""
    
    def has_first_inputs(self, incoming_edges: list[ExecutableEdgeV2]) -> bool:
        """Check if PersonJob has 'first' inputs."""
        return any(
            edge.target_input == "first" or edge.target_input.startswith("first.")
            for edge in incoming_edges
        )
    
    def should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        execution_context: ExecutionContext,
        has_special_inputs: bool = False
    ) -> bool:
        """Process edge based on whether it's a special 'first' input."""
        if has_special_inputs:
            # When there are 'first' inputs, only process those
            return edge.target_input == "first" or edge.target_input.startswith("first.")
        # Otherwise process all edges normally
        return True


class ConditionStrategy(NodeStrategy):
    """Strategy for Condition nodes."""
    pass


class NodeStrategyFactory:
    """Factory for creating node-type-specific strategies."""
    
    def __init__(self):
        self._strategies = {
            NodeType.PERSON_JOB: PersonJobStrategy(),
            NodeType.CONDITION: ConditionStrategy(),
        }
        self._default_strategy = NodeStrategy()
    
    def get_strategy(self, node_type: NodeType) -> NodeStrategy:
        """Get strategy for a specific node type."""
        return self._strategies.get(node_type, self._default_strategy)