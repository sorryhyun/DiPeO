
import re
from typing import Any, Dict, List, Tuple
from .output_processor import OutputProcessor

def render_prompt(template: str, variables: Dict[str, Any]) -> str:
    """Replace {{var}} with its value. Unknown names are left untouched."""
    def repl(m):
        key = m.group(1)
        return str(variables.get(key, m.group(0)))
    return re.sub(r"{{(\w+)}}", repl, template)


def resolve_inputs(nid: str, incoming: List[dict], context: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any]]:
    """Resolve incoming arrow values into vars_map and inputs list."""
    vars_map: Dict[str, Any] = {}
    inputs: List[Any] = []
    from ..run_graph import DiagramExecutor

    for e in incoming:
        src_id = e.get("source")
        value = context.get(src_id)
        if src_id == nid and value is None:
            continue

        arrow_id = e.get('id', '<unknown>')
        data = e.get('data', {})
        ctype = data.get('contentType', 'raw_text')

        label = data.get('label')
        
        if ctype == 'raw_text':
            # Extract text content if this is a PersonJob output
            processed_value = OutputProcessor.extract_value(value)
            var_name = label or f'raw_text_{arrow_id}'
        elif ctype == 'variable_in_object':
            object_key_path = data.get('objectKeyPath', '')
            if not object_key_path:
                raise ValueError(f"Arrow {arrow_id} with type 'variable_in_object' missing 'objectKeyPath'")
            processed_value = DiagramExecutor._extract_from_object(value, object_key_path)
            var_name = label or object_key_path.split('.')[-1]
        elif ctype == 'conversation_state':
            # For conversation_state, we need to provide the conversation history as Messages object
            if OutputProcessor.is_personjob_output(value):
                # This is output from a PersonJob node, extract conversation history
                processed_value = OutputProcessor.extract_conversation_history(value)
            elif isinstance(value, list) and all(isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in value):
                # Already properly formatted as Messages object
                processed_value = value
            else:
                # Fallback: create a simple message
                processed_value = [{"role": "user", "content": str(value)}]
            var_name = label or 'conversation_state'
        else:
            var_name = label or data.get('variableName')
            if not var_name:
                raise ValueError(f"Arrow {arrow_id} missing 'label' or 'variableName'")
            # Handle PersonJob output for default case
            if isinstance(value, dict) and value.get('_type') == 'personjob_output':
                processed_value = value.get('text', '')
            else:
                processed_value = value

        vars_map[var_name] = processed_value
        inputs.append(processed_value)

    return vars_map, inputs