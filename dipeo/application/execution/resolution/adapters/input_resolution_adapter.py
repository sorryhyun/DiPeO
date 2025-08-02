"""Adapter to make new interfaces work with existing TypedInputResolutionService.

This adapter allows gradual migration from the old input resolution
to the new interface-based approach.
"""

from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.execution.node_output import NodeOutputProtocol, ConditionOutput

from ..interfaces import (
    RuntimeInputResolver,
    ExecutionContext,
    NodeStrategyFactory,
    StandardNodeOutput,
    StandardTransformationEngine,
)


class ExecutionContextAdapter:
    """Adapts the existing parameters to the ExecutionContext protocol."""
    
    def __init__(
        self,
        node_outputs: dict[str, Any],
        node_exec_counts: dict[str, int] | None = None,
        current_node_id: str | None = None
    ):
        self._node_outputs = node_outputs
        self._node_exec_counts = node_exec_counts or {}
        self._current_node_id = current_node_id
    
    @property
    def node_exec_counts(self) -> dict[str, int]:
        return self._node_exec_counts
    
    @property  
    def is_first_execution(self) -> bool:
        if self._current_node_id:
            return self.get_node_exec_count(self._current_node_id) <= 1
        return True
    
    def get_node_exec_count(self, node_id: str) -> int:
        return self._node_exec_counts.get(node_id, 0)
    
    def has_node_output(self, node_id: str) -> bool:
        return node_id in self._node_outputs
    
    def get_node_output(self, node_id: str) -> Any:
        return self._node_outputs.get(node_id)


class RuntimeInputResolverAdapter(RuntimeInputResolver):
    """Adapts the new RuntimeInputResolver interface to work with existing code."""
    
    def __init__(self):
        self.strategy_factory = NodeStrategyFactory()
        self.transformation_engine = StandardTransformationEngine()
    
    def resolve_inputs(
        self,
        node_id: str,
        edges: list[Any],  # ExecutableEdge from existing code
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve inputs using the new interface approach."""
        inputs = {}
        
        # Get node to determine type and strategy
        # In real implementation, we'd get this from the diagram
        # For now, we'll determine from first edge
        node_type = self._infer_node_type(node_id, edges)
        strategy = self.strategy_factory.get_strategy(node_type)
        
        # Check for special inputs (e.g., PersonJob "first" inputs)
        has_special_inputs = False
        if node_type == NodeType.PERSON_JOB and hasattr(strategy, 'has_first_inputs'):
            has_special_inputs = strategy.has_first_inputs(edges)
        
        for edge in edges:
            # Create a mock node for the strategy
            mock_node = type('MockNode', (), {'id': node_id, 'type': node_type})()
            
            if not self.should_process_edge(edge, mock_node, context, has_special_inputs):
                continue
            
            # Get source output value
            value = self.get_edge_value(edge, context)
            if value is None:
                continue
            
            # Apply transformations
            transformed_value = self.apply_transformations(value, edge)
            
            # Get input key
            input_key = strategy.get_input_key(edge)
            inputs[input_key] = transformed_value
        
        return inputs
    
    def should_process_edge(
        self,
        edge: Any,
        node: Any,
        context: ExecutionContext,
        has_special_inputs: bool = False
    ) -> bool:
        """Determine if edge should be processed."""
        strategy = self.strategy_factory.create_strategy(node)
        return strategy.should_process_edge(edge, node, context, has_special_inputs)
    
    def get_edge_value(
        self,
        edge: Any,
        context: ExecutionContext  
    ) -> Any:
        """Extract value from edge's source node."""
        source_node_id = str(edge.source_node_id)
        source_output = context.get_node_output(source_node_id)
        
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
            # Legacy dict format - original only uses "value" field
            return StandardNodeOutput.from_value(source_output["value"])
        else:
            # Raw value
            return StandardNodeOutput.from_value(source_output)
    
    def apply_transformations(
        self,
        value: Any,
        edge: Any
    ) -> Any:
        """Apply transformation rules to a value."""
        # Handle StandardNodeOutput
        if isinstance(value, StandardNodeOutput):
            output_key = edge.source_output or "default"
            
            # Mimic original's behavior more closely
            if not isinstance(value.value, dict):
                # Non-dict values are wrapped as {"default": value}
                output_dict = {"default": value.value}
            else:
                output_dict = value.value
            
            # Check if the output has the requested key
            if output_key not in output_dict:
                if output_key == "default" and (not edge.source_output or edge.source_output == "default"):
                    # Use entire dict as value
                    actual_value = output_dict
                elif "default" in output_dict:
                    actual_value = output_dict["default"]
                else:
                    # Skip if no matching output - return None to signal skip
                    return None
            else:
                actual_value = output_dict[output_key]
        else:
            actual_value = value
        
        # Apply transformations if edge has them
        if hasattr(edge, 'data_transform') and edge.data_transform:
            actual_value = self.transformation_engine.transform(
                actual_value, 
                edge.data_transform
            )
        
        return actual_value
    
    def _infer_node_type(self, node_id: str, edges: list[Any]) -> NodeType:
        """Infer node type from edges - temporary helper."""
        # This is a simplified inference - in real implementation
        # we'd get the actual node from the diagram
        for edge in edges:
            target_input = edge.target_input or ""
            if target_input == "first" or target_input.endswith("_first"):
                return NodeType.PERSON_JOB
        
        # Default to PersonJob for now
        return NodeType.PERSON_JOB


class TypedInputResolutionServiceAdapter:
    """Adapter that makes the existing service use new interfaces internally."""
    
    def __init__(self):
        self.resolver = RuntimeInputResolverAdapter()
    
    def resolve_inputs_for_node(
        self,
        node_id: str,
        node_type: NodeType,
        diagram: ExecutableDiagram,
        node_outputs: dict[str, Any],
        node_exec_counts: dict[str, int] | None = None,
        node_memory_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve inputs using the new resolver with adapters."""
        # Get incoming edges
        incoming_edges = [
            edge for edge in diagram.edges 
            if str(edge.target_node_id) == node_id
        ]
        
        # Create execution context
        context = ExecutionContextAdapter(
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts,
            current_node_id=node_id
        )
        
        # Use new resolver
        return self.resolver.resolve_inputs(node_id, incoming_edges, context)