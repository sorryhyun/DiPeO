"""Standard runtime input resolver implementation.

This resolver handles the actual value resolution during diagram execution,
including node-specific strategies and data transformations.
"""

from typing import Any
import json
from uuid import uuid4

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode, ExecutableDiagram
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory

from dipeo.core.resolution import (
    NodeStrategyFactory,
    StandardNodeOutput,
    StandardTransformationEngine,
)


class StandardRuntimeResolver(RuntimeResolver):
    """Standard implementation of runtime input resolution.
    
    This resolver coordinates:
    1. Node-type-specific strategies for input handling
    2. Data transformation based on content types
    3. Edge filtering based on execution context
    """
    
    def __init__(self):
        self.strategy_factory = NodeStrategyFactory()
        self.transformation_engine = StandardTransformationEngine()
    
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

            # For PersonJob nodes with edges marked for first execution,
            # we need to map the input to the correct template variable name
            if node.type == NodeType.PERSON_JOB and edge.metadata and edge.metadata.get('is_first_execution'):
                # This edge was marked with _first suffix during compilation
                # The handle ID uses "first" to distinguish it from default input
                # But the template variable should be "default" (or a labeled name if provided)
                
                # Check if there's a label on the arrow (stored in metadata)
                if edge.metadata.get('label'):
                    # Use the arrow label as the template variable name
                    input_key = edge.metadata['label']
                else:
                    # No label, so use "default" as the template variable name
                    input_key = 'default'
            else:
                # Get input key from edge for non-PersonJob first execution cases
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
        
        # Handle pure Envelope instances (Phase 4 migration)
        if isinstance(source_output, Envelope):
            # Extract value directly from envelope body
            value = source_output.body
            
            # Special handling for condition outputs stored in envelope
            if source_output.content_type == "condition_result":
                # Extract branch data from envelope metadata
                branch_taken = source_output.meta.get("branch_taken")
                branch_data = source_output.meta.get("branch_data", {})
                if branch_taken == "true":
                    output_value = {"condtrue": branch_data}
                else:
                    output_value = {"condfalse": branch_data}
                return StandardNodeOutput.from_dict(output_value)
            
            return StandardNodeOutput.from_value(value)
        
        # If we reach here, source_output is not an Envelope (shouldn't happen)
        # Handle dict format or raw value as fallback
        if isinstance(source_output, dict) and "value" in source_output:
            # Dict format
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

            if output_key in output_dict:
                actual_value = output_dict[output_key]
            elif output_key == "default":
                # Special handling for default output
                if len(output_dict) == 1:
                    # If requesting default and only one output, use it
                    actual_value = next(iter(output_dict.values()))
                elif "default" in output_dict:
                    # Use explicit default key
                    actual_value = output_dict["default"]
                else:
                    # For multi-file DB read or similar cases, use the entire dict
                    # when requesting default and no explicit default key exists
                    actual_value = output_dict
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
    
    def resolve_single_input(
        self,
        node: ExecutableNode,
        input_name: str,
        edge: ExecutableEdgeV2,
        context: ExecutionContext
    ) -> Any:
        """Resolve a single input value through an edge."""
        # Get the value and apply transformations
        value = self._get_edge_value(edge, context)
        if value is not None:
            value = self._apply_transformations(value, edge)
        return value
    
    def extract_output_value(
        self,
        output: Envelope,
        output_name: str = "default"
    ) -> Any:
        """Extract a specific output value from a node output."""
        # Handle pure Envelope instances (Phase 4 migration)
        if isinstance(output, Envelope):
            # For envelopes with condition results
            if output.content_type == "condition_result":
                branch_taken = output.meta.get("branch_taken")
                branch_data = output.meta.get("branch_data", {})
                if branch_taken == "true" and output_name == "condtrue":
                    return branch_data
                elif branch_taken == "false" and output_name == "condfalse":
                    return branch_data
                return None
            
            # For regular envelopes
            if output_name == "default":
                return output.body
            # Try to extract from body if it's a dict
            if isinstance(output.body, dict):
                return output.body.get(output_name)
            return None
        
        # Should not reach here as output should always be an Envelope
        # Return None for safety
        return None
    
    def apply_transformation(
        self,
        value: Any,
        transformation_rules: dict[str, Any],
        source_context: dict[str, Any] | None = None
    ) -> Any:
        """Apply transformation rules to a value."""
        return self.transformation_engine.transform(value, transformation_rules)
    
    def register_transformation(
        self,
        name: str,
        rule: Any
    ) -> None:
        """Register a custom transformation rule."""
        # This would be implemented if we support custom transformations
        pass
    
    def resolve_default_value(
        self,
        node: ExecutableNode,
        input_name: str,
        input_type: str | None = None
    ) -> Any:
        """Get default value for an unconnected input."""
        # Most inputs default to None
        # Could be enhanced with node-specific defaults
        return None
    
    def resolve_conditional_input(
        self,
        node: ExecutableNode,
        edges: list[ExecutableEdgeV2],
        context: ExecutionContext,
        condition_key: str = "is_conditional"
    ) -> dict[str, Any]:
        """Resolve inputs that depend on conditional branches."""
        inputs = {}
        for edge in edges:
            # Check if edge is marked as conditional
            if edge.metadata and edge.metadata.get(condition_key):
                # Process conditional edge
                value = self._get_edge_value(edge, context)
                if value is not None:
                    transformed_value = self._apply_transformations(value, edge)
                    input_key = edge.target_input or 'default'
                    inputs[input_key] = transformed_value
        return inputs
    
    def validate_resolved_inputs(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate that resolved inputs meet node requirements."""
        errors = []
        
        # Basic validation - could be enhanced with node-specific rules
        if hasattr(node, 'required_inputs'):
            for required in node.required_inputs:
                if required not in inputs or inputs[required] is None:
                    errors.append(f"Missing required input: {required}")
        
        return len(errors) == 0, errors
    
    def get_transformation_chain(
        self,
        source_type: str,
        target_type: str
    ) -> list[Any] | None:
        """Get chain of transformations to convert between types."""
        # For now, we don't support transformation chains
        # This could be enhanced to find multi-step transformations
        return None
    
    async def resolve_as_envelopes(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram
    ) -> dict[str, Envelope]:
        """Resolve all inputs as envelopes.
        
        This is the main method for envelope-aware handlers to get their inputs.
        """
        resolved = {}
        trace_id = getattr(context, 'execution_id', str(uuid4()))
        
        # Get incoming edges for this node
        incoming_edges = self._get_incoming_edges(node, diagram)
        
        for edge in incoming_edges:
            # Get source output - use the proper method for TypedExecutionContext
            if hasattr(context, 'get_node_output'):
                source_output = context.get_node_output(edge.source_node_id)
            else:
                # Fall back for other context types
                source_output = getattr(context, 'get_output', lambda x: None)(str(edge.source_node_id))
            
            if source_output is None:
                continue
            
            # Convert to envelope if needed
            if isinstance(source_output, Envelope):
                envelope = source_output
            else:
                # Create envelopes from outputs
                from dipeo.core.execution.envelope import EnvelopeFactory
                # Extract value from source_output
                if hasattr(source_output, 'value'):
                    value = source_output.value
                else:
                    value = source_output
                    
                if isinstance(value, str):
                    envelopes = [EnvelopeFactory.text(value, produced_by=str(edge.source_node_id), trace_id=context.execution_id)]
                elif isinstance(value, (dict, list)):
                    envelopes = [EnvelopeFactory.json(value, produced_by=str(edge.source_node_id), trace_id=context.execution_id)]
                else:
                    envelopes = [EnvelopeFactory.text(str(value), produced_by=str(edge.source_node_id), trace_id=context.execution_id)]
                
                envelope = envelopes[0] if envelopes else None
            
            if envelope:
                # Apply transformations if needed
                envelope = await self._transform_envelope(
                    envelope, edge, node
                )
                
                # Apply iteration/branch filtering
                envelope = self._filter_by_iteration(
                    envelope, context, edge
                )
                
                if envelope:
                    # Store with edge label or target input
                    label = getattr(edge, 'label', None) or getattr(edge, 'target_input', None) or 'default'
                    resolved[label] = envelope
        
        # Add special inputs (conversation, variables, etc.)
        resolved.update(
            await self._resolve_special_inputs(node, context, trace_id)
        )
        
        return resolved
    
    def _get_incoming_edges(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram
    ) -> list[ExecutableEdgeV2]:
        """Get all edges targeting this node."""
        incoming = []
        for edge in diagram.edges:
            if edge.target_node_id == node.id:
                incoming.append(edge)
        return incoming
    
    async def _transform_envelope(
        self,
        envelope: Envelope,
        edge: ExecutableEdgeV2,
        target_node: ExecutableNode
    ) -> Envelope:
        """Apply edge transformations to envelope."""
        
        # Check if transformation needed based on edge transform_rules
        if hasattr(edge, 'transform_rules') and edge.transform_rules:
            # Handle common transformations
            if 'json_to_text' in edge.transform_rules:
                if envelope.content_type == "object":
                    text = json.dumps(envelope.body)
                    return EnvelopeFactory.text(
                        text,
                        produced_by=envelope.produced_by,
                        trace_id=envelope.trace_id
                    ).with_meta(**envelope.meta)
            
            elif 'text_to_json' in edge.transform_rules:
                if envelope.content_type == "raw_text":
                    try:
                        data = json.loads(envelope.body)
                        return EnvelopeFactory.json(
                            data,
                            produced_by=envelope.produced_by,
                            trace_id=envelope.trace_id
                        ).with_meta(**envelope.meta)
                    except json.JSONDecodeError:
                        # Keep as text if not valid JSON
                        pass
        
        return envelope
    
    def _filter_by_iteration(
        self,
        envelope: Envelope,
        context: ExecutionContext,
        edge: ExecutableEdgeV2
    ) -> Envelope | None:
        """Filter envelope by iteration/branch."""
        
        # Check iteration match
        if 'iteration' in envelope.meta:
            # Get current iteration for target node
            current_iteration = self._get_node_iteration(context, str(edge.target_node_id))
            if envelope.meta['iteration'] != current_iteration:
                return None
        
        # Check branch match
        if 'branch_id' in envelope.meta:
            active_branch = self._get_active_branch(context, str(edge.target_node_id))
            if envelope.meta['branch_id'] != active_branch:
                return None
        
        return envelope
    
    def _get_node_iteration(
        self,
        context: ExecutionContext,
        node_id: str
    ) -> int:
        """Get current iteration for a node."""
        # This would check the context for the current iteration count
        # For now, return 0 as default
        return 0
    
    def _get_active_branch(
        self,
        context: ExecutionContext,
        node_id: str
    ) -> str | None:
        """Get active branch for a node."""
        # This would check if node is in a conditional branch
        # For now, return None
        return None
    
    async def _resolve_special_inputs(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        trace_id: str
    ) -> dict[str, Envelope]:
        """Resolve special inputs like conversation state."""
        
        special = {}
        
        # Add conversation state if needed for PersonJob nodes
        if node.type == NodeType.PERSON_JOB and hasattr(node, 'use_conversation_memory'):
            if node.use_conversation_memory:
                person_id = getattr(node, 'person', None)
                if person_id:
                    conv_state = await self._get_conversation_state(
                        person_id, context
                    )
                    if conv_state:
                        special['_conversation'] = EnvelopeFactory.conversation(
                            conv_state,
                            produced_by="system",
                            trace_id=trace_id
                        )
        
        # Add variables
        if hasattr(context, 'variables') and context.variables:
            special['_variables'] = EnvelopeFactory.json(
                dict(context.variables),
                produced_by="system",
                trace_id=trace_id
            )
        
        return special
    
    async def _get_conversation_state(
        self,
        person_id: str,
        context: ExecutionContext
    ) -> dict | None:
        """Get conversation state for a person."""
        # This would fetch from conversation manager
        # For now, return None
        return None