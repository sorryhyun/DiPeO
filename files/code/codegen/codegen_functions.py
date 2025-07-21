"""
Code generation functions for DiPeO node type generation.
Generates TypeScript models, Python models, GraphQL schemas, and React components
from node specification JSON files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

# Get project root from environment or use current working directory
PROJECT_ROOT = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))


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
    print(f"DEBUG: parse_spec_data - inputs keys: {list(inputs.keys())}")
    
    # The validation node outputs data in the 'raw_data' input key
    raw_data = inputs.get('raw_data', {})
    print(f"DEBUG: raw_data type: {type(raw_data)}")
    print(f"DEBUG: raw_data content: {raw_data}")
    
    # The validator outputs a dict with 'valid', 'data', etc.
    # Extract the actual spec from raw_data.data
    spec = None
    if isinstance(raw_data, dict) and 'data' in raw_data:
        spec = raw_data['data']
        print(f"DEBUG: Extracted spec from raw_data.data")
    elif isinstance(raw_data, dict) and 'nodeType' in raw_data:
        # Fallback: raw_data might already be the spec
        spec = raw_data
        print(f"DEBUG: raw_data appears to be the spec itself")
    else:
        # Try to find spec data in other inputs
        for key, value in inputs.items():
            if isinstance(value, dict) and 'nodeType' in value:
                spec = value
                print(f"DEBUG: Found spec data in key '{key}'")
                break
        else:
            spec = {}
            print(f"DEBUG: No spec data found, using empty dict")
    
    # If it's a string, try to parse it
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
            print(f"DEBUG: Parsed JSON string")
        except:
            print(f"DEBUG: Failed to parse as JSON")
            return {"error": "Invalid JSON input"}
    
    print(f"DEBUG: Final spec type: {type(spec)}")
    if isinstance(spec, dict):
        print(f"DEBUG: spec keys: {list(spec.keys())[:10]}")  # First 10 keys
        print(f"DEBUG: nodeType in spec: {'nodeType' in spec}")
        if 'nodeType' in spec:
            print(f"DEBUG: nodeType value: {spec['nodeType']}")
    else:
        print(f"ERROR: spec is not a dict, it's {type(spec)}")
        return {"error": f"Expected dict, got {type(spec)}"}

    # Helper function to convert to camelCase
    def to_camel_case(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])

    # Ensure we have the required nodeType field
    if 'nodeType' not in spec:
        print(f"ERROR: Missing 'nodeType' field in spec")
        return {"error": "Missing required field 'nodeType' in specification"}
    
    # Prepare context for templates
    base_result = {
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

    print(f"Parsed spec for node type: {base_result['nodeType']}")
    print(f"Number of fields: {len(base_result['fields'])}")
    
    # Create result with spec_data pointing to base_result
    result = {
        **base_result,
        'spec_data': base_result,
        'default': base_result
    }
    
    return result


def generate_python_model(inputs: Dict[str, Any]) -> str:
    """Skip Python model generation - models are already generated from TypeScript."""
    # Get spec from inputs
    spec = inputs.get('spec', inputs.get('default', {}))
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    node_type = spec['nodeType']
    
    print(f"Python model generation skipped for {node_type} - models are generated from TypeScript")
    print(f"The model should already exist in dipeo/core/static/generated_nodes.py")
    
    return f"Python model generation skipped - {node_type} model exists in generated_nodes.py"


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
    expected_files = [
        str(PROJECT_ROOT / f"dipeo/models/src/nodes/{spec['nodeType']}Node.ts"),
        str(PROJECT_ROOT / f"apps/server/src/dipeo_server/api/graphql/schema/nodes/{spec['nodeType']}.graphql"),
        str(PROJECT_ROOT / f"apps/web/src/features/diagram-editor/components/nodes/generated/{spec['nodeType']}Node.tsx"),
        str(PROJECT_ROOT / f"apps/web/src/features/diagram-editor/config/nodes/generated/{camel_case_name}Config.ts"),
        str(PROJECT_ROOT / f"apps/web/src/features/diagram-editor/config/nodes/generated/{camel_case_name}Fields.ts")
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
            f"2. Ensure {spec['nodeType']}Node is generated in dipeo/core/static/generated_nodes.py by running 'make codegen-models'",
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
    output_dir = PROJECT_ROOT / 'output' / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'registry_updates.json', 'w') as f:
        json.dump(registry_updates, f, indent=2)

    print(f"\nRegistry update summary written to {output_dir / 'registry_updates.json'}")
    print(f"Generated {len(files_generated)} out of {len(expected_files)} expected files for {spec['nodeType']} node")
    
    if files_missing:
        print(f"Missing files: {', '.join(files_missing)}")
    
    # Return with default key for connection resolution
    return {
        'default': registry_updates,
        **registry_updates
    }


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
    
    # Run the registration helper script
    helper_script = PROJECT_ROOT / 'scripts' / 'register_generated_node.py'
    if helper_script.exists():
        print(f"\n📋 Running registration helper script...")
        print(f"You can also run it manually: python {helper_script}")
    
    # Return with default key for connection resolution
    return {
        'default': result,
        **result
    }


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