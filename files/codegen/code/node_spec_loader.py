"""
Simplified node specification loader.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_node_spec(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load a node specification JSON file."""
    spec_path = inputs.get('node_spec_path', inputs.get('default', {}).get('node_spec_path', ''))
    if not spec_path:
        return {"error": "No node_spec_path provided"}
    
    try:
        with open(spec_path, 'r') as f:
            return {"default": json.load(f)}
    except FileNotFoundError:
        return {"error": f"File not found: {spec_path}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}