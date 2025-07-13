# Typed input resolution for ExecutableDiagram

from typing import Dict, Any, Optional, TYPE_CHECKING

from dipeo.models import NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.core.static.executable_diagram import ExecutableDiagram
    from dipeo.application.execution.arrow.arrow_processor import ArrowProcessor


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
        inputs = {}
        
        # Find all edges pointing to this node
        incoming_edges = [
            edge for edge in diagram.edges 
            if str(edge.target_node_id) == node_id
        ]
        
        for edge in incoming_edges:
            # Check if we should process this edge
            if not self._should_process_edge(edge, node_type, node_exec_counts):
                continue
            
            # Get source node output
            source_node_id = str(edge.source_node_id)
            source_output = node_outputs.get(source_node_id)
            if not source_output:
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
                    continue
            
            # Get the input key where this should be placed
            input_key = edge.target_input or "default"
            
            # Apply any transformations if specified
            if edge.data_transform:
                # Apply transformation rules from edge metadata
                pass
            
            # Store the input
            inputs[input_key] = node_output.value[output_key]
        
        return inputs
    
    def _should_process_edge(
        self,
        edge,
        node_type: NodeType,
        node_exec_counts: Optional[Dict[str, int]] = None
    ) -> bool:
        """Check if an edge should be processed based on node type and execution state."""
        # PersonJob nodes have special handling for "first" inputs
        if node_type == NodeType.person_job:
            node_id = str(edge.target_node_id)
            exec_count = node_exec_counts.get(node_id, 0) if node_exec_counts else 0
            
            # On first execution, only process "first" inputs
            if exec_count == 0 and edge.target_input == "first":
                return True
            # On subsequent executions, skip "first" inputs
            elif exec_count > 0 and edge.target_input != "first":
                return True
            else:
                return False
        
        # For all other node types, process all edges
        return True