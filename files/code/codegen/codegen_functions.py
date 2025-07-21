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
            "update_registry",
            "register_node_types",
            "read_generated_files"
        ],
        "description": "Functions for generating code from node specifications"
    }


def parse_spec_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the spec data from validation output and prepare context for templates."""
    # Get the raw data from inputs
    raw_data = inputs.get('raw_data', inputs.get('default', {}))
    
    print(f"DEBUG: parse_spec_data - inputs keys: {list(inputs.keys())}")
    print(f"DEBUG: parse_spec_data - raw_data type: {type(raw_data)}")
    
    # Parse the spec data from validation output
    if isinstance(raw_data, dict) and 'data' in raw_data:
        spec = raw_data['data']
        print(f"DEBUG: Found wrapped data, extracted spec")
    elif isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
            if isinstance(parsed, dict) and 'data' in parsed:
                spec = parsed['data']
                print(f"DEBUG: Parsed string and found wrapped data")
            else:
                spec = parsed
                print(f"DEBUG: Parsed string directly")
        except:
            print(f"DEBUG: Failed to parse as JSON, using raw string")
            spec = raw_data
    else:
        spec = raw_data
        print(f"DEBUG: Using raw_data as-is")
    
    print(f"DEBUG: Final spec type: {type(spec)}")
    if isinstance(spec, dict):
        print(f"DEBUG: spec keys: {list(spec.keys())[:5]}")  # First 5 keys
        print(f"DEBUG: nodeType in spec: {'nodeType' in spec}")

    # Helper function to convert to camelCase
    def to_camel_case(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])

    # Prepare context for templates
    result = {
        'spec': spec,
        'nodeType': spec['nodeType'],
        'camelCase': to_camel_case(spec['nodeType']),
        'displayName': spec.get('displayName', spec['nodeType']),
        'fields': spec.get('fields', []),
        'handles': spec.get('handles', {}),
        'category': spec.get('category', 'custom'),
        'icon': spec.get('icon', '📦'),
        'color': spec.get('color', '#6b7280'),
        'description': spec.get('description', '')
    }

    # Keep boolean and other values as-is for the safeJson helper
    # The template helper will handle proper formatting

    print(f"Parsed spec for node type: {result['nodeType']}")
    
    return result


def generate_python_model(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a placeholder Python model for the node type."""
    # Get spec from inputs
    spec = inputs.get('spec', inputs.get('default', {}))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    node_type = spec['nodeType']
    node_type_capitalized = node_type.capitalize()
    
    # Create output directory - using the actual Python models location
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent.parent  # Navigate from files/code/codegen to project root
    output_dir = project_root / 'dipeo/core/static/nodes'
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
            
            # Check if field is required (handle both boolean and string)
            if isinstance(required, str):
                required = required.lower() == 'true'
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
    print(f"DEBUG: update_registry - inputs keys: {list(inputs.keys())}")
    
    # Get spec from inputs
    spec = inputs.get('spec', inputs.get('default', {}))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    # Helper function to convert to camelCase
    def to_camel_case(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    camel_case_name = to_camel_case(spec['nodeType'])
    
    # Create list of expected generated files
    # Use project root for absolute paths
    project_root = Path(__file__).parent.parent.parent.parent
    expected_files = [
        str(project_root / f"dipeo/models/src/nodes/{spec['nodeType']}Node.ts"),
        str(project_root / f"dipeo/core/static/nodes/{spec['nodeType']}_node.py"), 
        str(project_root / f"apps/server/src/dipeo_server/api/graphql/schema/nodes/{spec['nodeType']}.graphql"),
        str(project_root / f"apps/web/src/features/diagram-editor/components/nodes/generated/{spec['nodeType']}Node.tsx"),
        str(project_root / f"apps/web/src/features/diagram-editor/config/nodes/generated/{camel_case_name}Config.ts"),
        str(project_root / f"apps/web/src/features/diagram-editor/config/nodes/generated/{camel_case_name}Fields.ts")
    ]
    
    # Check which files were actually generated
    files_generated = []
    files_missing = []
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            files_generated.append(file_path)
        else:
            files_missing.append(file_path)
    
    # Create registry update summary
    registry_updates = {
        'nodeType': spec['nodeType'],
        'files_generated': files_generated,
        'files_missing': files_missing,
        'next_steps': [
            f"1. Add {spec['nodeType']} to NODE_TYPE_MAP in dipeo/models/src/conversions.ts",
            f"2. Import and register {spec['nodeType']}Node in dipeo/core/static/generated_nodes.py",
            f"3. Add {spec['nodeType']} to the GraphQL schema union types",
            f"4. Register the node config in the frontend node registry",
            f"5. Run 'make codegen' to regenerate all derived files",
            f"6. Add handler implementation in dipeo/application/execution/handlers/{spec['nodeType']}.py"
        ],
        'generation_summary': {
            'total_expected': len(expected_files),
            'total_generated': len(files_generated),
            'success_rate': f"{(len(files_generated) / len(expected_files) * 100):.1f}%"
        }
    }

    # Write summary file
    os.makedirs('output/generated', exist_ok=True)
    with open('output/generated/registry_updates.json', 'w') as f:
        json.dump(registry_updates, f, indent=2)

    print(f"\nRegistry update summary written to output/generated/registry_updates.json")
    print(f"Generated {len(files_generated)} out of {len(expected_files)} expected files for {spec['nodeType']} node")
    
    if files_missing:
        print(f"Missing files: {', '.join(files_missing)}")
    
    return registry_updates


def register_node_types(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Register the new node type in various system files."""
    # Get inputs
    spec = inputs.get('spec', {})
    registry_updates = inputs.get('registry_updates', {})
    
    if isinstance(spec, str):
        spec = json.loads(spec)
    if isinstance(registry_updates, str):
        registry_updates = json.loads(registry_updates)
    
    node_type = spec.get('nodeType', '')
    pascal_case = node_type.capitalize()
    
    files_updated = []
    errors = []
    
    print(f"Starting node registration for: {node_type}")
    
    # For now, just log what needs to be done manually
    manual_steps = [
        f"1. Add {node_type} to NODE_TYPE_MAP in dipeo/models/src/conversions.ts",
        f"2. Import and register {pascal_case}Node in dipeo/core/static/generated_nodes.py", 
        f"3. Add {node_type} to the GraphQL schema union types in apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql",
        f"4. Register the node config in apps/web/src/features/diagram/config/nodeRegistry.ts",
        f"5. Create handler in dipeo/application/execution/handlers/{node_type}.py"
    ]
    
    result = {
        "success": True,
        "message": f"Generated files for {node_type} node. Manual registration required.",
        "filesUpdated": files_updated,
        "manualSteps": manual_steps,
        "generatedFiles": registry_updates.get('files_generated', [])
    }
    
    print(f"Registration complete. Manual steps required:")
    for step in manual_steps:
        print(f"  {step}")
    
    return result


def read_generated_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Read all generated files for verification."""
    # Get the registry updates which contains file paths
    registry_updates = inputs.get('registry_updates', {})
    files_generated = registry_updates.get('files_generated', [])
    
    file_contents = {}
    read_errors = []
    
    for file_path in files_generated:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents[file_path] = {
                    'content': content,
                    'size': len(content),
                    'lines': content.count('\n') + 1
                }
        except Exception as e:
            read_errors.append({
                'file': file_path,
                'error': str(e)
            })
    
    result = {
        'files_read': len(file_contents),
        'file_contents': file_contents,
        'read_errors': read_errors,
        'summary': f"Successfully read {len(file_contents)} out of {len(files_generated)} files"
    }
    
    if read_errors:
        print(f"Errors reading files: {[e['file'] for e in read_errors]}")
    
    return result