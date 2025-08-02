"""Direct implementation of RuntimeInputResolver for runtime value resolution.

This resolver handles the actual value resolution during diagram execution,
including node-specific strategies and data transformations.
"""

from typing import Any

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.application.resolution.input_resolution import RuntimeInputResolver, TransformRules
from dipeo.core.execution.executable_diagram import ExecutableEdgeV2, ExecutableNode, ExecutableDiagram
from dipeo.core.execution.node_output import NodeOutputProtocol, ConditionOutput

from dipeo.application.execution.resolution.interfaces import (
    NodeStrategyFactory,
    StandardNodeOutput,
    StandardTransformationEngine,
)


class ExecutionContext:
    """Context for runtime execution state."""
    
    def __init__(
        self,
        node_outputs: dict[str | NodeID, Any],
        node_exec_counts: dict[str | NodeID, int] | None = None,
        current_node_id: str | NodeID | None = None
    ):
        self.node_outputs = node_outputs
        self.node_exec_counts = node_exec_counts or {}
        self.current_node_id = current_node_id
    
    def get_node_execution_count(self, node_id: str | NodeID) -> int:
        """Get execution count for a node."""
        return self.node_exec_counts.get(node_id, 0)
    
    def is_first_execution(self, node_id: str | NodeID) -> bool:
        """Check if this is the first execution of a node."""
        return self.get_node_execution_count(node_id) <= 1
    
    def has_node_output(self, node_id: str | NodeID) -> bool:
        """Check if a node has produced output."""
        return node_id in self.node_outputs
    
    def get_node_output(self, node_id: str | NodeID) -> Any:
        """Get output from a node."""
        return self.node_outputs.get(node_id)


class StandardRuntimeInputResolver(RuntimeInputResolver):
    """Standard implementation of runtime input resolution.
    
    This resolver coordinates:
    1. Node-type-specific strategies for input handling
    2. Data transformation based on content types
    3. Edge filtering based on execution context
    """
    
    def __init__(self):
        self.strategy_factory = NodeStrategyFactory()
        self.transformation_engine = StandardTransformationEngine()
    
    async def resolve_input_value(
        self,
        target_node_id: NodeID,
        target_input: str,
        node_outputs: dict[NodeID, Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve a specific input value for a node.
        
        This is a simplified interface for resolving single inputs.
        For full node input resolution, use resolve_node_inputs.
        """
        # Find the edge that provides this input
        # In practice, this would be passed from the compiler
        # For now, we'll return None as this is a simplified interface
        return None
    
    def resolve_node_inputs(
        self,
        node: ExecutableNode,
        incoming_edges: list[ExecutableEdgeV2],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve all inputs for a node using strategies and transformations.
        
        This is the main entry point for runtime input resolution.
        """
        inputs = {}
        
        # Get strategy for this node type
        strategy = self.strategy_factory.get_strategy(node.type)
        
        # Check for special inputs (e.g., PersonJob "first" inputs)
        has_special_inputs = self._has_special_inputs(node, incoming_edges, strategy)
        
        for edge in incoming_edges:
            if not self._should_process_edge(edge, node, context, strategy, has_special_inputs):
                continue
            
            # Get source output value
            value = self._get_edge_value(edge, context)
            if value is None:
                continue
            
            # Apply transformations
            transformed_value = self._apply_transformations(value, edge)
            if transformed_value is None:
                continue
            
            # Get input key from edge
            input_key = edge.target_input or 'default'
            inputs[input_key] = transformed_value
        
        return inputs
    
    def _has_special_inputs(
        self,
        node: ExecutableNode,
        edges: list[ExecutableEdgeV2],
        strategy: Any
    ) -> bool:
        """Check if node has special inputs like PersonJob 'first' inputs."""
        if node.type == NodeType.PERSON_JOB and hasattr(strategy, 'has_first_inputs'):
            return strategy.has_first_inputs(edges)
        return False
    
    def _should_process_edge(
        self,
        edge: ExecutableEdgeV2,
        node: ExecutableNode,
        context: ExecutionContext,
        strategy: Any,
        has_special_inputs: bool
    ) -> bool:
        """Determine if an edge should be processed based on strategy."""
        return strategy.should_process_edge(edge, node, context, has_special_inputs)
    
    def _get_edge_value(
        self,
        edge: ExecutableEdgeV2,
        context: ExecutionContext
    ) -> Any:
        """Extract value from edge's source node output."""
        source_output = context.get_node_output(edge.source_node_id)
        
        if not source_output:
            return None
        
        # Convert to StandardNodeOutput for consistent handling
        if isinstance(source_output, NodeOutputProtocol):
            if isinstance(source_output, ConditionOutput):
                # Special handling for condition outputs
                if source_output.value:  # True branch
                    output_value = {"condtrue": source_output.true_output or {}}
                else:  # False branch
                    output_value = {"condfalse": source_output.false_output or {}}
                return StandardNodeOutput.from_dict(output_value)
            else:
                # All other protocol outputs
                return StandardNodeOutput.from_value(source_output.value)
        elif isinstance(source_output, dict) and "value" in source_output:
            # Legacy dict format
            return StandardNodeOutput.from_value(source_output["value"])
        else:
            # Raw value
            return StandardNodeOutput.from_value(source_output)
    
    def _apply_transformations(
        self,
        value: Any,
        edge: ExecutableEdgeV2
    ) -> Any:
        """Apply transformation rules from edge to value."""
        # Handle StandardNodeOutput
        if isinstance(value, StandardNodeOutput):
            output_key = edge.source_output or "default"
            
            # Extract the actual value based on output key
            if not isinstance(value.value, dict):
                # Non-dict values are wrapped
                output_dict = {"default": value.value}
            else:
                output_dict = value.value
            
            # Get the specific output
            if output_key in output_dict:
                actual_value = output_dict[output_key]
            elif output_key == "default" and len(output_dict) == 1:
                # If requesting default and only one output, use it
                actual_value = next(iter(output_dict.values()))
            elif "default" in output_dict:
                # Fallback to default
                actual_value = output_dict["default"]
            else:
                # No matching output
                return None
        else:
            actual_value = value
        
        # Apply transformations if edge has them
        if edge.transform_rules:
            actual_value = self.transformation_engine.transform(
                actual_value,
                edge.transform_rules
            )
        
        return actual_value