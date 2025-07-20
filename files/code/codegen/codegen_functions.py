"""
Code generation functions for DiPeO node type generation.
Generates TypeScript models, Python models, GraphQL schemas, and React components
from node specification JSON files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point - provides information about available functions.
    """
    return {
        "message": "DiPeO Code Generation Functions",
        "available_functions": [
            "parse_spec_data",
            "generate_python_model", 
            "update_registry"
        ],
        "description": "Functions for generating code from node specifications"
    }


def parse_spec_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the spec data from validation output and prepare context for templates."""
    # Get the raw data from inputs
    raw_data = inputs.get('raw_data', inputs.get('default', {}))
    
    # Parse the spec data from validation output
    if isinstance(raw_data, dict) and 'data' in raw_data:
        spec = raw_data['data']
    elif isinstance(raw_data, str):
        spec = json.loads(raw_data)
    else:
        spec = raw_data

    # Prepare context for templates
    result = {
        'spec': spec,
        'nodeType': spec['nodeType'],
        'displayName': spec.get('displayName', spec['nodeType']),
        'fields': spec.get('fields', []),
        'handles': spec.get('handles', {}),
        'category': spec.get('category', 'custom'),
        'icon': spec.get('icon', '📦'),
        'color': spec.get('color', '#6b7280'),
        'description': spec.get('description', '')
    }

    # Convert Python booleans to JavaScript format for templates
    for field in result['fields']:
        if 'required' in field:
            field['required'] = 'true' if field['required'] else 'false'
        if 'defaultValue' in field:
            if isinstance(field['defaultValue'], str):
                field['defaultValue'] = f"'{field['defaultValue']}'"
            elif field['defaultValue'] is None:
                field['defaultValue'] = 'null'

    print(f"Parsed spec for node type: {result['nodeType']}")
    print(f"[parse_spec_data] Returning dict with keys: {list(result.keys())}")
    print(f"[parse_spec_data] nodeType value: {result['nodeType']}")
    
    # Also save to file for debugging
    import json
    import os
    os.makedirs('output/debug', exist_ok=True)
    with open('output/debug/parse_spec_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    return result


def generate_python_model(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a placeholder Python model for the node type."""
    # Get spec from inputs
    spec = inputs.get('spec', inputs.get('default', {}))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    node_type = spec['nodeType']
    node_type_capitalized = node_type.capitalize()
    
    # Create output directory
    output_dir = Path('output/generated/python')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate Python model content
    model_content = f"""# Generated Python model for {node_type} node
from dataclasses import dataclass, field
from typing import Optional, Literal
from dipeo.core.static.generated_nodes import BaseNode
from dipeo.models import NodeType

@dataclass
class {node_type_capitalized}Node(BaseNode):
    type: NodeType = field(default=NodeType.{node_type}, init=False)
"""

    # Add fields based on spec
    if 'fields' in spec:
        for field_spec in spec['fields']:
            field_name = field_spec['name']
            field_type = field_spec.get('type', 'string')
            required = field_spec.get('required', False)
            
            # Map field types to Python types
            type_map = {
                'string': 'str',
                'number': 'float',
                'boolean': 'bool',
                'enum': f"Literal{field_spec.get('values', [])}"
            }
            python_type = type_map.get(field_type, 'str')
            
            if not required:
                python_type = f"Optional[{python_type}]"
                
            model_content += f"    {field_name}: {python_type}\n"
    
    # Write the model file
    output_path = output_dir / f"{node_type}_node.py"
    with open(output_path, 'w') as f:
        f.write(model_content)
    
    print(f"Generated Python model for {node_type} node at {output_path}")
    return f"Generated Python model at {output_path}"


def update_registry(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Create registry update summary with all generated files and next steps."""
    # Get spec from inputs
    spec = inputs.get('spec', inputs.get('default', {}))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    # Create registry update summary
    registry_updates = {
        'nodeType': spec['nodeType'],
        'files_generated': [
            f"output/generated/{spec['nodeType']}Node.ts",
            f"output/generated/python/{spec['nodeType']}_node.py", 
            f"output/generated/{spec['nodeType']}.graphql",
            f"output/generated/{spec['nodeType']}Node.tsx",
            f"output/generated/{spec['nodeType']}Config.ts",
            f"output/generated/{spec['nodeType']}Fields.ts"
        ],
        'next_steps': [
            f"1. Add {spec['nodeType']} to NODE_TYPE_MAP in dipeo/models/src/conversions.ts",
            f"2. Import and register {spec['nodeType']}Node in dipeo/core/static/generated_nodes.py",
            f"3. Add {spec['nodeType']} to the GraphQL schema union types",
            f"4. Register the node config in the frontend node registry",
            f"5. Run 'make codegen' to regenerate all derived files",
            f"6. Add handler implementation in dipeo/application/execution/handlers/{spec['nodeType']}.py"
        ]
    }

    # Write summary file
    os.makedirs('output/generated', exist_ok=True)
    with open('output/generated/registry_updates.json', 'w') as f:
        json.dump(registry_updates, f, indent=2)

    print(f"\nRegistry update summary written to output/generated/registry_updates.json")
    print(f"Generated {len(registry_updates['files_generated'])} files for {spec['nodeType']} node")
    
    return registry_updates