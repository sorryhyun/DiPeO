"""Domain service for input resolution logic."""

from typing import Dict, Any, Optional
import logging

from dipeo.models import DomainDiagram, DomainArrow, NodeType

log = logging.getLogger(__name__)


class InputResolutionService:
    """Service for managing input resolution business logic."""
    
    def should_process_arrow(
        self,
        arrow: DomainArrow,
        target_node_type: str,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if an arrow should be processed for input resolution.
        
        Business rules:
        - Person job nodes with "first" handle only process on first execution
        - All other arrows are always processed
        """
        # Special handling for person_job nodes
        if target_node_type == NodeType.person_job:
            # Parse handle from target HandleID
            from dipeo.models import parse_handle_id
            target_node_id, target_handle, _ = parse_handle_id(arrow.target)
            
            target_exec_count = node_exec_counts.get(target_node_id, 0) if node_exec_counts else 0
            
            # If this is a "first" handle and not the first execution, skip it
            if target_handle == "first" and target_exec_count > 0:
                log.debug(
                    f"Skipping 'first' handle arrow {arrow.id} for person_job "
                    f"(execution count: {target_exec_count})"
                )
                return False
        
        return True
    
    def should_skip_condition_branch(
        self,
        arrow: DomainArrow,
        source_node_type: str,
        condition_result: Optional[bool],
    ) -> bool:
        """Determine if a condition branch should be skipped.
        
        Business rules:
        - Skip "true" branch if condition is false
        - Skip "false" branch if condition is true
        - Process all arrows if condition result is unknown
        """
        if source_node_type != NodeType.condition:
            return False
        
        if condition_result is None:
            # If we don't know the condition result, process all arrows
            return False
        
        # Determine which branch this arrow represents
        # Parse handle from source HandleID
        from dipeo.models import parse_handle_id
        _, source_handle, _ = parse_handle_id(arrow.source)
        
        if source_handle == "condtrue" and not condition_result:
            log.debug(f"Skipping true branch arrow {arrow.id} (condition was false)")
            return True
        elif source_handle == "condfalse" and condition_result:
            log.debug(f"Skipping false branch arrow {arrow.id} (condition was true)")
            return True
        
        return False
    
    def resolve_inputs_for_node(
        self,
        node_id: str,
        node_type: str,
        diagram: DomainDiagram,
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Resolve all inputs for a given node.
        
        This combines outputs from all upstream nodes based on arrows,
        respecting the business rules for arrow processing.
        """
        inputs = {}
        
        # Find all arrows pointing to this node
        # Parse handle IDs to get node IDs
        from dipeo.models import parse_handle_id, extract_node_id_from_handle
        incoming_arrows = []
        for arrow in diagram.arrows:
            target_node_id = extract_node_id_from_handle(arrow.target)
            if target_node_id == node_id:
                incoming_arrows.append(arrow)
        
        for arrow in incoming_arrows:
            # Check if we should process this arrow
            if not self.should_process_arrow(arrow, node_type, node_exec_counts):
                continue
            
            # Parse source node ID from HandleID
            source_node_id, source_handle, _ = parse_handle_id(arrow.source)
            
            # Get source node output
            source_output = node_outputs.get(source_node_id, {})
            if not source_output:
                continue
            
            # Get source node to check its type
            source_node = next(
                (node for node in diagram.nodes if node.id == source_node_id),
                None
            )
            if not source_node:
                continue
            
            # Check if this is a condition branch we should skip
            if source_node.type == NodeType.condition:
                # Extract condition result from output
                condition_result = None
                if isinstance(source_output, dict):
                    metadata = source_output.get("metadata", {})
                    if isinstance(metadata, dict):
                        condition_result = metadata.get("condition_result")
                
                if self.should_skip_condition_branch(
                    arrow, source_node.type.value, condition_result
                ):
                    continue
            
            # Parse target handle for input key
            _, target_handle, _ = parse_handle_id(arrow.target)
            
            # Add the output to inputs
            # Use label as the input key, or target handle as fallback
            input_key = arrow.label or target_handle or arrow.id
            
            # Extract the appropriate value from source output
            if isinstance(source_output, dict) and "value" in source_output:
                # This is a NodeOutput structure
                value_dict = source_output["value"]
                
                # For condition nodes, get the branch-specific output
                if source_node.type == NodeType.condition:
                    if source_handle in value_dict:
                        inputs[input_key] = value_dict[source_handle]
                else:
                    # For other nodes, use source handle or default
                    handle_key = source_handle or "default"
                    if handle_key in value_dict:
                        inputs[input_key] = value_dict[handle_key]
                    elif "default" in value_dict:
                        inputs[input_key] = value_dict["default"]
            else:
                # Direct value
                inputs[input_key] = source_output
        
        return inputs