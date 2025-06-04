"""
Utility functions for executor operations.
Extracted from BaseExecutor to simplify the executor pattern.
"""
from typing import Dict, Any, List, TYPE_CHECKING
import re

# Validation functions have been moved to validator.py

if TYPE_CHECKING:
    from ..engine import ExecutionContext


def get_input_values(node: Dict[str, Any], context: 'ExecutionContext') -> Dict[str, Any]:
    """
    Get input values for a node from incoming arrows.
    
    Args:
        node: The node to get inputs for
        context: Execution context with arrow information
        
    Returns:
        Dictionary mapping arrow labels to their values
    """
    inputs = {}
    node_id = node["id"]
    incoming = context.incoming_arrows.get(node_id, [])
    
    # Import OutputProcessor here to avoid circular imports
    from ...utils.output_processor import OutputProcessor
    
    for arrow in incoming:
        source_id = arrow["source"]
        # Handle both direct label and nested data.label structure
        label = arrow.get("label", "")
        if not label and "data" in arrow:
            label = arrow["data"].get("label", "")
        
        # Get the output from the source node
        if source_id in context.node_outputs and label:
            output = context.node_outputs[source_id]
            
            # Check arrow content type
            content_type = arrow.get("contentType")
            if not content_type and "data" in arrow:
                content_type = arrow["data"].get("contentType")
            
            # Handle content type
            if content_type == "conversation_state":
                # Pass the full structured output with conversation history
                inputs[label] = output
            else:
                # Default to raw text extraction
                inputs[label] = OutputProcessor.extract_value(output)
    
    return inputs


def substitute_variables(text: str, variables: Dict[str, Any]) -> str:
    """
    Substitute {{variable}} patterns in text.
    
    Args:
        text: Text containing variable placeholders
        variables: Dictionary of variable values
        
    Returns:
        Text with variables substituted
    """
    if not text:
        return text
    
    # Import OutputProcessor and json here to avoid circular imports
    from ...utils.output_processor import OutputProcessor
    import json
    
    def replace_var(match):
        var_name = match.group(1)
        value = variables.get(var_name, match.group(0))
        
        # Check if this is a structured PersonJob output with conversation history
        if OutputProcessor.is_personjob_output(value):
            # Check if the variable name suggests we want conversation history
            if 'conversation' in var_name.lower() or 'history' in var_name.lower():
                # For conversation variables, we want to show the text content
                # which represents the conversation that happened
                text_value = OutputProcessor.extract_value(value)
                return text_value if text_value else ""
            else:
                # Default to extracting just the text
                value = OutputProcessor.extract_value(value)
        
        # Convert to string, handling special cases
        if value is None:
            return ""
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, dict)):
            # For complex objects, serialize to JSON
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    # Replace {{variable}} patterns
    return re.sub(r'{{(\w+)}}', replace_var, text)


def has_incoming_connection(node: Dict[str, Any], context: 'ExecutionContext') -> bool:
    """Check if node has any incoming connections"""
    node_id = node["id"]
    return node_id in context.incoming_arrows and len(context.incoming_arrows[node_id]) > 0


def has_outgoing_connection(node: Dict[str, Any], context: 'ExecutionContext') -> bool:
    """Check if node has any outgoing connections"""
    node_id = node["id"]
    return node_id in context.outgoing_arrows and len(context.outgoing_arrows[node_id]) > 0


def get_upstream_nodes(node: Dict[str, Any], context: 'ExecutionContext') -> List[str]:
    """Get IDs of all upstream (source) nodes"""
    node_id = node["id"]
    upstream = []
    
    for arrow in context.incoming_arrows.get(node_id, []):
        source_id = arrow["source"]
        if source_id not in upstream:
            upstream.append(source_id)
    
    return upstream


def get_downstream_nodes(node: Dict[str, Any], context: 'ExecutionContext') -> List[str]:
    """Get IDs of all downstream (target) nodes"""
    node_id = node["id"]
    downstream = []
    
    for arrow in context.outgoing_arrows.get(node_id, []):
        target_id = arrow["target"]
        if target_id not in downstream:
            downstream.append(target_id)
    
    return downstream