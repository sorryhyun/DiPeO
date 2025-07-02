"""Template substitution utilities."""

import re
from typing import Any, Dict, List, Tuple


def substitute_template(template: str, values: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Substitute {{placeholders}} in template with values.
    
    Args:
        template: Template string containing {{placeholders}}
        values: Dictionary of values to substitute
        
    Returns:
        tuple: (substituted_string, list_of_missing_keys, list_of_used_keys)
    """
    missing_keys = []
    used_keys = []
    
    def replacer(match):
        key = match.group(1)
        if key in values:
            used_keys.append(key)
            return str(values[key])
        else:
            missing_keys.append(key)
            return match.group(0)  # Keep original placeholder
    
    # Match {{key}} pattern
    pattern = r'\{\{(\w+)\}\}'
    result = re.sub(pattern, replacer, template)
    
    return result, missing_keys, used_keys