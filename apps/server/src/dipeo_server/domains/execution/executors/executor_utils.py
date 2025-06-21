"""
Utility functions for executor operations.
Extracted from BaseExecutor to simplify the executor pattern.
"""
from typing import Dict, Any, List, TYPE_CHECKING
import re

# Validation functions have been moved to validator.py

if TYPE_CHECKING:
    from .types import Ctx


def get_input_values(node: Dict[str, Any], context: 'Ctx', target_handle_filter: str = None) -> Dict[str, Any]:
    inputs = {}
    node_id = node["id"]
    incoming = context.graph.incoming.get(node_id, [])
    
    # Import OutputProcessor here to avoid circular imports
    from dipeo_server.core.processors import OutputProcessor
    
    for arrow in incoming:
        if target_handle_filter:
            target_handle = arrow.t_handle
            # Handle ends with filter (e.g., "-first") or exact match
            if not (target_handle.endswith(f"-{target_handle_filter}") or 
                    target_handle == target_handle_filter):
                continue
        
        source_id = arrow.source
        label = arrow.label
        
        if source_id in context.outputs and label:
            output = context.outputs[source_id]
            
            content_type = "conversation_state" if "conversation" in arrow.label.lower() else None

            if content_type == "conversation_state":
                inputs[label] = output
            else:
                inputs[label] = OutputProcessor.extract_value(output)
    
    return inputs


def substitute_variables(text: str, variables: Dict[str, Any], evaluation_mode: bool = False) -> str:
    if not text:
        return text
    
    # Import OutputProcessor and json here to avoid circular imports
    from dipeo_server.core.processors import OutputProcessor
    import json
    
    def replace_var(match):
        var_name = match.group(1) or match.group(2)  # {{var}} or ${var}
        value = variables.get(var_name, match.group(0))
        
        if OutputProcessor.is_personjob_output(value):
            if 'conversation' in var_name.lower() or 'history' in var_name.lower():
                # Show conversation text content
                text_value = OutputProcessor.extract_value(value)
                return text_value if text_value else ""
            else:
                value = OutputProcessor.extract_value(value)
        
        if value is None:
            return "None" if evaluation_mode else ""
        elif isinstance(value, bool):
            if evaluation_mode:
                return "True" if value else "False"
            else:
                return str(value).lower()
        elif isinstance(value, str):
            return f'"{value}"' if evaluation_mode else value
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    pattern = r'{{(\w+)}}|\${(\w+)}'  # {{variable}} or ${variable}
    return re.sub(pattern, replace_var, text)


def has_incoming_connection(node: Dict[str, Any], context: 'Ctx') -> bool:
    """Check if node has any incoming connections"""
    node_id = node["id"]
    return node_id in context.graph.incoming and len(context.graph.incoming[node_id]) > 0


def has_outgoing_connection(node: Dict[str, Any], context: 'Ctx') -> bool:
    """Check if node has any outgoing connections"""
    node_id = node["id"]
    return node_id in context.graph.outgoing and len(context.graph.outgoing[node_id]) > 0


def get_upstream_nodes(node: Dict[str, Any], context: 'Ctx') -> List[str]:
    """Get IDs of all upstream (source) nodes"""
    node_id = node["id"]
    upstream = []
    
    for arrow in context.graph.incoming.get(node_id, []):
        source_id = arrow.source
        if source_id not in upstream:
            upstream.append(source_id)
    
    return upstream


def get_downstream_nodes(node: Dict[str, Any], context: 'Ctx') -> List[str]:
    """Get IDs of all downstream (target) nodes"""
    node_id = node["id"]
    downstream = []
    
    for arrow in context.graph.outgoing.get(node_id, []):
        target_id = arrow.target
        if target_id not in downstream:
            downstream.append(target_id)
    
    return downstream