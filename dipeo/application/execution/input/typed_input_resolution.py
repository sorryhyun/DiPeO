# Typed input resolution for ExecutableDiagram

from typing import Dict, Any, Optional, TYPE_CHECKING

from dipeo.models import NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.core.static.executable_diagram import ExecutableDiagram
    from dipeo.utils.arrow.arrow_processor import ArrowProcessor


class TypedInputResolutionService:
    """Input resolution service that works with typed ExecutableDiagram."""
    
    def __init__(self, arrow_processor: "ArrowProcessor"):
        self.arrow_processor = arrow_processor
    
    def resolve_inputs_for_node(
        self,
        node_id: str,
        node_type: NodeType,
        diagram: "ExecutableDiagram",
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
        node_memory_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Resolve inputs for a node using ExecutableDiagram edges."""
        import logging
        log = logging.getLogger(__name__)
        
        inputs = {}
        
        # Find all edges pointing to this node
        incoming_edges = [
            edge for edge in diagram.edges 
            if str(edge.target_node_id) == node_id
        ]
        
        log.debug(f"Node {node_id} has {len(incoming_edges)} incoming edges")
        log.debug(f"Node outputs available: {list(node_outputs.keys())}")
        
        for edge in incoming_edges:
            # Check if we should process this edge
            log.debug(f"Processing edge: source={edge.source_node_id}, target_input={edge.target_input}")
            if not self._should_process_edge(edge, node_type, node_exec_counts):
                log.debug(f"Edge skipped by _should_process_edge")
                continue
            
            # Get source node output
            source_node_id = str(edge.source_node_id)
            source_output = node_outputs.get(source_node_id)
            log.debug(f"Source node {source_node_id} output: {source_output}")
            if not source_output:
                log.debug(f"No output found for source node {source_node_id}")
                continue
            
            # Handle different source_output formats
            if isinstance(source_output, NodeOutput):
                node_output = source_output
            elif isinstance(source_output, dict) and "value" in source_output:
                # Dict with proper structure - convert to NodeOutput
                node_output = NodeOutput(
                    value=source_output["value"],
                    metadata=source_output.get("metadata"),
                    node_id=source_output.get("node_id", source_node_id),
                    executed_nodes=source_output.get("executed_nodes")
                )
            else:
                # Legacy format - wrap as NodeOutput
                node_output = NodeOutput(
                    value={"default": source_output},
                    metadata={},
                    node_id=source_node_id,
                    executed_nodes=None
                )
            
            # Get the specific output key
            output_key = edge.source_output or "default"
            
            # Check if the output has the requested key
            if output_key not in node_output.value:
                # Try default if specific key not found
                if "default" in node_output.value:
                    output_key = "default"
                else:
                    # Skip if no matching output
                    log.debug(f"No matching output key '{output_key}' in node output: {node_output.value}")
                    continue
            
            # Get the input key where this should be placed
            # Use label from metadata if available, otherwise use target_input
            log.debug(f"Edge metadata: {edge.metadata}")
            input_key = edge.metadata.get("label") or edge.target_input or "default"
            
            log.debug(f"Adding input: key='{input_key}', value from output_key='{output_key}'")
            
            # Apply any transformations if specified
            if edge.data_transform:
                # Wrap the input with memory configuration from edge
                wrapped_input = {
                    "value": node_output.value[output_key],
                    "arrow_metadata": {
                        "arrow_id": edge.id,
                        "source_node_id": str(edge.source_node_id),
                        "target_node_id": str(edge.target_node_id),
                    }
                }
                
                # Add memory hints from edge data_transform
                if "forgetting_mode" in edge.data_transform and edge.data_transform["forgetting_mode"]:
                    wrapped_input["memory_hints"] = {
                        "forget_mode": edge.data_transform["forgetting_mode"],
                        "should_apply": edge.data_transform.get("include_in_memory", True),
                    }
                
                # Store the wrapped input
                inputs[input_key] = wrapped_input
            else:
                # Store the input directly
                inputs[input_key] = node_output.value[output_key]
        
        return inputs
    
    def _should_process_edge(
        self,
        edge,
        node_type: NodeType,
        node_exec_counts: Optional[Dict[str, int]] = None
    ) -> bool:
        """Check if an edge should be processed based on node type and execution state."""
        import logging
        log = logging.getLogger(__name__)
        
        # PersonJob nodes have special handling for "first" inputs
        if node_type == NodeType.person_job:
            node_id = str(edge.target_node_id)
            exec_count = node_exec_counts.get(node_id, 0) if node_exec_counts else 0
            
            log.debug(f"PersonJob edge check: target_input={edge.target_input}, exec_count={exec_count}")
            
            # On first execution, only process inputs ending with "_first" or exactly "first"
            if exec_count == 0 and edge.target_input and (edge.target_input == "first" or edge.target_input.endswith("_first")):
                return True
            # On subsequent executions, skip "_first" inputs
            elif exec_count > 0 and edge.target_input and not (edge.target_input == "first" or edge.target_input.endswith("_first")):
                return True
            else:
                return False
        
        # For all other node types, process all edges
        return True