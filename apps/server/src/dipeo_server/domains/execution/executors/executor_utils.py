"""
Utility functions for executor operations.
Extracted from BaseExecutor to simplify the executor pattern.
"""
from typing import Dict, Any, List, TYPE_CHECKING, Optional
import re
import logging

# Validation functions have been moved to validator.py

if TYPE_CHECKING:
    from .types import Ctx
    from dipeo_domain import ExecutionContext

logger = logging.getLogger(__name__)

# Regex pattern for {{var}} placeholders
_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


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
    
    # First handle {{variable}} and ${variable} patterns
    pattern = r'{{(\w+)}}|\${(\w+)}'  
    result = re.sub(pattern, replace_var, text)
    
    # Then handle $variable syntax (without braces)
    for k, v in variables.items():
        result = result.replace(f"${k}", str(v))
    
    return result


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


def safe_eval(expr: str, inputs: Dict[str, Any], ctx: 'ExecutionContext') -> bool:
    """Tiny, dependency-free expression evaluator."""
    namespace: Dict[str, Any] = {"executionCount": ctx.exec_cnt, **inputs}

    # Flatten previous node outputs for easy access
    for node_id, output in ctx.outputs.items():
        if isinstance(output, dict):
            namespace.update(output)
        else:
            namespace[node_id] = output

    # Replace {{var}} placeholders early
    def _tpl(match: re.Match[str]) -> str:
        val = namespace.get(match.group(1))
        return _fmt(val)

    expr = _VAR_PATTERN.sub(_tpl, expr)

    # Replace bare identifiers with their literal value
    for key, val in namespace.items():
        expr = re.sub(rf"\b{re.escape(key)}\b", _fmt(val), expr)

    # Normalise JS-style logical operators to Python
    expr = (
        expr.replace("&&", " and ")
        .replace("||", " or ")
        .replace("===", "==")
        .replace("!==", "!=")
    )

    try:
        return bool(eval(expr, {"__builtins__": {}}, {}))  # nosec B307 - controlled input
    except Exception:
        logger.debug("Evaluation error for expression %s", expr, exc_info=True)
        return False


def _fmt(val: Any) -> str:
    """Return a Python literal representation suitable for eval."""
    if val is None:
        return "None"
    if isinstance(val, str):
        return f'"{val}"'
    return str(val)


def process_inputs(inputs: Dict[str, Any]) -> List[Any]:
    """Process inputs to extract values and handle special output types."""
    if not inputs:
        return []
    
    from dipeo_server.core.processors import OutputProcessor
    
    processed = []
    for value in inputs.values():
        # Use OutputProcessor to properly unwrap structured outputs
        unwrapped = OutputProcessor.unwrap(value)
        processed.append(unwrapped)
    
    return processed


def get_api_key(api_key_id: str, context: 'ExecutionContext') -> Optional[str]:
    """Get API key from execution context."""
    if not hasattr(context, 'api_keys'):
        return None
    
    api_key_info = context.api_keys.get(api_key_id)
    if isinstance(api_key_info, dict):
        return api_key_info.get('key')
    return api_key_info if isinstance(api_key_info, str) else None


def log_action(logger: logging.Logger, node_id: str, action: str, **extra) -> None:
    """Consistent logging helper for node actions."""
    log_data = {
        "node_id": node_id,
        "action": action,
        **extra
    }
    logger.info(f"[{node_id}] {action}", extra=log_data)