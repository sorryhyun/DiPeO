# Typed input resolution for ExecutableDiagram

from typing import TYPE_CHECKING, Any

from dipeo.models import NodeType
from dipeo.core.execution.node_output import NodeOutputProtocol, ConditionOutput

if TYPE_CHECKING:
    from dipeo.core.static.executable_diagram import ExecutableDiagram


class TypedInputResolutionService:
    """Input resolution service that works with typed ExecutableDiagram."""
    
    def __init__(self):
        pass
    
    def resolve_inputs_for_node(
        self,
        node_id: str,
        node_type: NodeType,
        diagram: "ExecutableDiagram",
        node_outputs: dict[str, Any],
        node_exec_counts: dict[str, int] | None = None,
        node_memory_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve inputs for a node using ExecutableDiagram edges."""
        import logging
        log = logging.getLogger(__name__)
        
        inputs = {}
        
        # Find all edges pointing to this node
        incoming_edges = [
            edge for edge in diagram.edges 
            if str(edge.target_node_id) == node_id
        ]

        # For PersonJob nodes on first execution, check if any "first" inputs exist
        has_first_inputs = False
        if node_type == NodeType.person_job:
            exec_count = node_exec_counts.get(node_id, 0) if node_exec_counts else 0
            if exec_count == 1:
                has_first_inputs = any(
                    edge.target_input and (edge.target_input == "first" or edge.target_input.endswith("_first"))
                    for edge in incoming_edges
                )

        for edge in incoming_edges:
            # Check if we should process this edge
            should_process = self._should_process_edge(edge, node_type, node_exec_counts, has_first_inputs)

            if not should_process:
                continue
            
            # Get source node output
            source_node_id = str(edge.source_node_id)
            source_output = node_outputs.get(source_node_id)
            if not source_output:
                continue
            
            # Handle different source_output formats
            if isinstance(source_output, NodeOutputProtocol):
                # Protocol output - extract value based on type
                if isinstance(source_output, ConditionOutput):
                    # For condition outputs, create dict with branch keys
                    if source_output.value:  # True branch
                        output_value = {"condtrue": source_output.true_output or {}}
                    else:  # False branch
                        output_value = {"condfalse": source_output.false_output or {}}
                else:
                    # Regular protocol output - get value directly
                    output_value = source_output.value
                    # Wrap non-dict values
                    if not isinstance(output_value, dict):
                        output_value = {"default": output_value}
            elif isinstance(source_output, dict) and "value" in source_output:
                # Dict with proper structure
                output_value = source_output["value"]
                if not isinstance(output_value, dict):
                    output_value = {"default": output_value}
            else:
                # Raw value - wrap as dict
                output_value = {"default": source_output}
            
            # Get the specific output key
            output_key = edge.source_output or "default"
            
            # Check if the output has the requested key
            if output_key not in output_value:
                # Try default if specific key not found
                if "default" in output_value:
                    output_key = "default"
                else:
                    # Skip if no matching output
                    continue
            
            # Get the input key where this should be placed
            # Use label from metadata if available, otherwise use target_input
            input_key = edge.metadata.get("label") or edge.target_input or "default"

            # Apply any transformations if specified
            if edge.data_transform:
                # Check if this is a conversation_state content type
                if edge.data_transform.get('content_type') == 'conversation_state':
                    # For conversation_state, pass the conversation data directly
                    value = output_value[output_key]
                    if isinstance(value, dict) and 'messages' in value:
                        # Pass the messages directly to the target node
                        inputs[input_key] = value
                    else:
                        inputs[input_key] = value
                else:
                    # Pass the value directly without memory configuration
                    inputs[input_key] = output_value[output_key]
            else:
                # Store the input directly
                inputs[input_key] = output_value[output_key]
        
        return inputs
    
    def _should_process_edge(
        self,
        edge,
        node_type: NodeType,
        node_exec_counts: dict[str, int] | None = None,
        has_first_inputs: bool = False
    ) -> bool:
        """Check if an edge should be processed based on node type and execution state."""
        import logging
        log = logging.getLogger(__name__)
        
        # PersonJob nodes have special handling for "first" inputs
        if node_type == NodeType.person_job:
            node_id = str(edge.target_node_id)
            exec_count = node_exec_counts.get(node_id, 0) if node_exec_counts else 0

            # On first execution (exec_count == 1 because it's incremented before execution),
            # handle "first" inputs specially
            if exec_count == 1:
                # Special case: Always process conversation_state inputs from condition nodes
                # These provide context for judging/decision-making
                if hasattr(edge, 'data_transform') and edge.data_transform:
                    if edge.data_transform.get('content_type') == 'conversation_state':
                        return True
                
                # If there are "first" inputs, only process those
                if has_first_inputs:
                    return edge.target_input and (edge.target_input == "first" or edge.target_input.endswith("_first"))
                # If no "first" inputs exist, fall back to processing default inputs
                else:
                    # Process edges without target_input (default) or explicitly "default"
                    return not edge.target_input or edge.target_input == "default"
            # On subsequent executions, process all non-_first inputs
            else:
                # Process edges without target_input (regular edges) or non-_first inputs
                return not edge.target_input or not (edge.target_input == "first" or edge.target_input.endswith("_first"))
        
        # For all other node types, process all edges
        return True