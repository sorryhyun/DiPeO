"""Refactored input resolution using the new interface-based approach.

This module demonstrates how to use the new interfaces for cleaner
separation of concerns between compile-time and runtime resolution.
"""

import logging
from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.core.static.executable_diagram import ExecutableDiagram

from .interfaces import (
    RuntimeInputResolver,
    ExecutionContext,
    NodeStrategyFactory,
    StandardNodeOutput,
    StandardTransformationEngine,
)
from .adapters import ExecutionContextAdapter


class RefactoredInputResolutionService:
    """Input resolution service using the new interface-based approach."""
    
    def __init__(self):
        self.runtime_resolver = RefactoredRuntimeResolver()
        self.logger = logging.getLogger(__name__)
    
    def resolve_inputs_for_node(
        self,
        node_id: str,
        node_type: NodeType,
        diagram: ExecutableDiagram,
        node_outputs: dict[str, Any],
        node_exec_counts: dict[str, int] | None = None,
        node_memory_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve inputs for a node using the refactored approach."""
        # Create execution context
        context = ExecutionContextAdapter(
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts,
            current_node_id=node_id
        )
        
        # Get node from diagram
        node = diagram.get_node(node_id)
        if not node:
            self.logger.warning(f"Node {node_id} not found in diagram")
            return {}
        
        # Get incoming edges
        incoming_edges = diagram.get_incoming_edges(node_id)
        
        # Resolve inputs using runtime resolver
        return self.runtime_resolver.resolve_inputs(
            node_id=node_id,
            node=node,
            edges=incoming_edges,
            context=context
        )


class RefactoredRuntimeResolver(RuntimeInputResolver):
    """Clean implementation of runtime input resolution."""
    
    def __init__(self):
        self.strategy_factory = NodeStrategyFactory()
        self.transformation_engine = StandardTransformationEngine()
        self.logger = logging.getLogger(__name__)
    
    def resolve_inputs(
        self,
        node_id: str,
        node: Any,  # ExecutableNode
        edges: list[Any],  # list[ExecutableEdge]
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve runtime input values for a node."""
        inputs = {}
        
        # Get strategy for node type
        strategy = self.strategy_factory.create_strategy(node)
        
        # Check for special inputs (e.g., PersonJob "first" inputs)
        has_special_inputs = self._check_for_special_inputs(node, edges, strategy)
        
        # Process each incoming edge
        for edge in edges:
            if not self.should_process_edge(edge, node, context, has_special_inputs):
                self.logger.debug(
                    f"Skipping edge {edge.id} for node {node_id} "
                    f"(exec_count={context.get_node_exec_count(node_id)})"
                )
                continue
            
            # Get value from source node
            value = self.get_edge_value(edge, context)
            if value is None:
                self.logger.debug(f"No output from source node {edge.source_node_id}")
                continue
            
            # Apply transformations
            transformed_value = self.apply_transformations(value, edge)
            
            # Get input key and store value
            input_key = strategy.get_input_key(edge)
            inputs[input_key] = transformed_value
            
            self.logger.debug(
                f"Resolved input '{input_key}' for node {node_id} "
                f"from edge {edge.id}"
            )
        
        return inputs
    
    def should_process_edge(
        self,
        edge: Any,
        node: Any,
        context: ExecutionContext,
        has_special_inputs: bool = False
    ) -> bool:
        """Determine if an edge should be processed."""
        strategy = self.strategy_factory.create_strategy(node)
        return strategy.should_process_edge(edge, node, context, has_special_inputs)
    
    def get_edge_value(
        self,
        edge: Any,
        context: ExecutionContext
    ) -> Any:
        """Extract the actual value from an edge's source node."""
        source_output = context.get_node_output(str(edge.source_node_id))
        if not source_output:
            return None
        
        # Convert to StandardNodeOutput for consistent handling
        node_output = self._normalize_output(source_output)
        
        # Extract the requested output
        output_key = edge.source_output or "default"
        
        # Smart extraction: check outputs dict first
        if output_key in node_output.outputs:
            return node_output.outputs[output_key]
        elif output_key == "default":
            # For default key, return the primary value
            return node_output.value
        else:
            # Fallback to default if specific key not found
            return node_output.outputs.get("default", node_output.value)
    
    def apply_transformations(
        self,
        value: Any,
        edge: Any
    ) -> Any:
        """Apply transformation rules to a value."""
        if hasattr(edge, 'data_transform') and edge.data_transform:
            return self.transformation_engine.transform(value, edge.data_transform)
        return value
    
    def _check_for_special_inputs(
        self,
        node: Any,
        edges: list[Any],
        strategy: Any
    ) -> bool:
        """Check if node has special inputs that affect processing."""
        if node.type == NodeType.PERSON_JOB and hasattr(strategy, 'has_first_inputs'):
            return strategy.has_first_inputs(edges)
        return False
    
    def _normalize_output(self, output: Any) -> StandardNodeOutput:
        """Normalize various output formats to StandardNodeOutput."""
        from dipeo.core.execution.node_output import NodeOutputProtocol, ConditionOutput
        
        # Check if it's a mock with value attribute (for testing)
        if hasattr(output, 'value') and not isinstance(output, dict):
            # Treat as NodeOutputProtocol
            if isinstance(output, ConditionOutput):
                # Special handling for condition outputs
                if output.value:  # True branch
                    output_dict = {"condtrue": output.true_output or {}}
                else:  # False branch
                    output_dict = {"condfalse": output.false_output or {}}
                return StandardNodeOutput.from_dict(output_dict)
            else:
                # Standard protocol outputs - handle dict values specially
                if isinstance(output.value, dict):
                    return StandardNodeOutput(
                        value=output.value,
                        outputs=output.value,  # Use the dict as outputs
                        metadata={}
                    )
                else:
                    return StandardNodeOutput(
                        value=output.value,
                        outputs={"default": output.value},
                        metadata={}
                    )
        elif isinstance(output, dict) and "value" in output:
            # Enhanced dict format - smarter extraction
            # If it has outputs field, use that; otherwise treat value as outputs
            if "outputs" in output:
                return StandardNodeOutput(
                    value=output["value"],
                    outputs=output["outputs"],
                    metadata=output.get("metadata", {})
                )
            else:
                return StandardNodeOutput.from_dict(output)
        else:
            # Raw value - if it's a dict, treat it as outputs directly
            if isinstance(output, dict):
                return StandardNodeOutput(
                    value=output,
                    outputs=output,
                    metadata={}
                )
            else:
                return StandardNodeOutput.from_value(output)