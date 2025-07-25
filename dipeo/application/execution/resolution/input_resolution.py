# Typed input resolution for ExecutableDiagram

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import NodeType
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
            
            # Extract value from source output
            if isinstance(source_output, NodeOutputProtocol):
                if isinstance(source_output, ConditionOutput):
                    # Special handling for condition outputs
                    if source_output.value:  # True branch
                        output_value = {"condtrue": source_output.true_output or {}}
                    else:  # False branch
                        output_value = {"condfalse": source_output.false_output or {}}
                else:
                    # All other protocol outputs - get value directly
                    output_value = source_output.value
            elif isinstance(source_output, dict) and "value" in source_output:
                # Legacy dict format
                output_value = source_output["value"]
            else:
                # Raw value
                output_value = source_output
            
            # Ensure output_value is a dict for key access
            if not isinstance(output_value, dict):
                output_value = {"default": output_value}
            
            output_key = edge.source_output or "default"
            
            # Debug logging
            # Check if the output has the requested key
            if output_key not in output_value:
                # For edges with default output key and no "default" in the output,
                # use the entire output value as the context
                if output_key == "default" and (not edge.source_output or edge.source_output == "default"):
                    # Use the entire output value as is
                    value = output_value
                elif "default" in output_value:
                    output_key = "default"
                    value = output_value[output_key]
                else:
                    # Skip if no matching output
                    continue
            else:
                value = output_value[output_key]
            
            # Get the input key where this should be placed
            input_key = edge.metadata.get("label") or edge.target_input or "default"

            # Apply transformations or pass value directly
            # Note: value might already be set above for the entire output case
            
            if edge.data_transform:
                content_type = edge.data_transform.get('content_type')
                
                if content_type == 'object' and isinstance(value, str):
                    # Try to parse JSON strings for object content type
                    if value.strip() and value.strip()[0] in '{[':
                        try:
                            import json
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            log.debug(f"Could not parse JSON for object content type")
                
            
            inputs[input_key] = value
        
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
            if exec_count == 1:
                # Special case: Always process conversation_state inputs from condition nodes
                if hasattr(edge, 'data_transform') and edge.data_transform:
                    if edge.data_transform.get('content_type') == 'conversation_state':
                        return True
                
                # If there are "first" inputs, only process those
                if has_first_inputs:
                    return edge.target_input and (edge.target_input == "first" or edge.target_input.endswith("_first"))
                else:
                    return not edge.target_input or edge.target_input == "default"
            else:
                return not edge.target_input or not (edge.target_input == "first" or edge.target_input.endswith("_first"))
        
        return True