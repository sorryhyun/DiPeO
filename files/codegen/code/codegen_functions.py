"""
Simplified code generation functions for DiPeO node type generation.
"""

import json
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point - provides information about available functions.
    """
    return {
        "message": "DiPeO Code Generation Functions",
        "available_functions": [
            "parse_spec_data_with_paths"
        ],
        "description": "Functions for generating code from node specifications"
    }


def parse_spec_data_with_paths(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse spec data and add output paths."""
    # Get spec from inputs
    spec = inputs.get('raw_data', inputs.get('spec', inputs))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    if not isinstance(spec, dict) or 'nodeType' not in spec:
        return {"error": "Invalid spec data - missing nodeType"}
    
    # Simple case conversion
    node_type = spec['nodeType']
    camel_case = node_type[0].lower() + ''.join(w.capitalize() for w in node_type.split('_')[1:])
    
    # Add output paths
    spec['output_paths'] = {
        'typescript_model': f"dipeo/models/src/nodes/{node_type}Node.ts",
        'graphql_schema': f"apps/server/src/dipeo_server/api/graphql/schema/nodes/{node_type}.graphql",
        'react_component': f"apps/web/src/__generated__/nodes/{node_type}NodeForm.tsx",
        'node_config': f"apps/web/src/__generated__/nodes/{node_type}NodeConfig.ts",
        'field_config': f"apps/web/src/__generated__/fields/{node_type}FieldConfigs.ts",
        'static_node': f"dipeo/core/static/nodes/{node_type.lower()}_node.py"
    }
    
    return spec


# Removed generate_python_model, update_registry, register_node_types functions
# These have been replaced by the simplified codegen.py