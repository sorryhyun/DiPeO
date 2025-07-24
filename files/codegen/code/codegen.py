"""
Simplified codegen module - replaces complex multi-file structure.

Core functionality:
1. Load node specification JSON
2. Render Jinja2 templates  
3. Write output files
4. Print manual registration steps
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to import from files/codegen/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from files.codegen.paths import (
    PROJECT_ROOT,
    SPECS_DIR,
    TEMPLATES_DIR,
    TEMP_DIR,
    NODE_REGISTRY_PATH,
    TEMPLATES,
    get_output_paths,
    ensure_temp_dir,
)

# Import utilities
from .utils import (
    create_jinja_env,
    snake_case,
    camel_case,
    pascal_case,
    emoji_to_icon_name,
    typescript_type_filter,
    python_type_filter,
    python_default_filter,
    graphql_type_filter,
    zod_schema_filter,
    default_value_filter,
    humanize_filter,
    ui_field_type_filter,
)

# Ensure temp dir exists
ensure_temp_dir()


# Main functions
def load_node_spec(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load node specification from JSON file."""
    spec_path = inputs.get('node_spec_path', '')
    if not spec_path:
        return {'error': 'No node_spec_path provided'}
    
    spec_file = Path(spec_path)
    if not spec_file.exists():
        # Try relative to spec dir
        spec_file = SPECS_DIR / spec_path
        if not spec_file.suffix:
            spec_file = spec_file.with_suffix('.json')
    
    if not spec_file.exists():
        return {'error': f'Spec file not found: {spec_file}'}
    
    return json.loads(spec_file.read_text())

def load_all_node_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load all node specifications from a directory or single file."""
    print(f"📂 Loading node specs with inputs: {list(inputs.keys())}")
    print(f"📂 Full inputs: {inputs}")
    
    # Write debug info to file
    debug_file = Path(".temp/codegen_debug.txt")
    debug_file.parent.mkdir(exist_ok=True)
    with open(debug_file, 'a') as f:
        f.write(f"\n=== load_all_node_specs called ===\n")
        f.write(f"Inputs: {inputs}\n")
    
    # Can accept either node_spec_path (single) or node_specs_dir (directory)
    single_path = inputs.get('node_spec_path', '')
    dir_path = inputs.get('node_specs_dir', '')
    
    # Default to specifications directory if nothing provided
    if not single_path and not dir_path:
        dir_path = 'files/codegen/specifications/nodes'
        print(f"📁 Using default directory: {dir_path}")
    
    specs = []
    
    if single_path:
        # Load single spec (backward compatible)
        result = load_node_spec({'node_spec_path': single_path})
        if 'error' not in result:
            specs.append({'node_spec': result})
    else:
        # Load all specs from directory
        spec_dir = Path(dir_path)
        if not spec_dir.is_absolute():
            spec_dir = SPECS_DIR if dir_path == 'files/codegen/specifications/nodes' else Path(dir_path)
        
        if not spec_dir.exists():
            return {'error': f'Directory not found: {spec_dir}'}
        
        # Find all JSON files in the directory
        for spec_file in sorted(spec_dir.glob('*.json')):
            try:
                spec_data = json.loads(spec_file.read_text())
                specs.append({'node_spec': spec_data})
            except Exception as e:
                # Skip invalid files but log them
                print(f"Warning: Failed to load {spec_file}: {e}")
    
    if not specs:
        return {'error': 'No valid node specifications found'}
    
    # Merge with existing state and return
    return {
        **inputs,  # Preserve all existing state
        'specs': specs,
        'total_nodes': len(specs)
    }

def parse_spec_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse spec data and add output paths."""
    spec = inputs.get('raw_data', inputs)
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    node_type = spec.get('nodeType', '')
    if not node_type:
        return {'error': 'No nodeType in spec'}
    
    # Add case variations for templates
    spec['nodeTypeSnake'] = snake_case(node_type)
    spec['nodeTypeCamel'] = camel_case(node_type)
    spec['nodeTypePascal'] = pascal_case(node_type)
    
    # Get output paths for this node type
    spec['output_paths'] = get_output_paths(node_type, spec)
    
    return spec

def render_template(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generic template rendering function."""
    template_name = inputs.get('template')
    output_path = inputs.get('output_path')
    spec_data = inputs.get('spec_data', {})
    
    if not template_name or not output_path:
        return {'error': 'Missing template or output_path'}
    
    if isinstance(spec_data, str):
        spec_data = json.loads(spec_data)
    
    # Use create_jinja_env from utilities
    env = create_jinja_env(str(TEMPLATES_DIR))
    
    # Add additional filters specific to codegen
    env.filters['typescript_type'] = typescript_type_filter
    env.filters['python_type'] = python_type_filter
    env.filters['python_default'] = python_default_filter
    env.filters['graphql_type'] = graphql_type_filter
    env.filters['zod_schema'] = zod_schema_filter
    env.filters['default_value'] = default_value_filter
    env.filters['humanize'] = humanize_filter
    env.filters['ui_field_type'] = ui_field_type_filter
    env.filters['quote'] = lambda s: f'"{s}"'
    env.filters['emoji_to_icon'] = emoji_to_icon_name
    env.filters['escape_js'] = lambda s: str(s).replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
    
    # Render template
    template = env.get_template(template_name)
    content = template.render(spec_data=spec_data, **spec_data)
    
    # Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    
    return {
        'success': True,
        'output_path': str(output_path),
        'message': f"Rendered {template_name} to {output_path}"
    }

def generate_all(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate all files for a node specification."""
    spec = parse_spec_data(inputs)
    if 'error' in spec:
        return {**inputs, 'error': spec['error']}
    
    # Map template names to their output paths
    templates = [
        ('typescript_model', spec['output_paths']['typescript_model']),
        ('graphql_schema', spec['output_paths']['graphql_schema']),
        # React components are not used - all nodes use ConfigurableNode
        # ('react_component', spec['output_paths']['react_component']),
        ('node_config', spec['output_paths']['node_config']),
        ('field_config', spec['output_paths']['field_config']),
        ('static_nodes', spec['output_paths']['static_node'])
    ]
    
    generated_files = []
    for template_name, output_path in templates:
        # Get the template path from our constants
        template_path = TEMPLATES.get(template_name)
        if not template_path:
            print(f"Warning: Unknown template {template_name}")
            continue
        
        result = render_template({
            'template': template_path,
            'output_path': output_path,
            'spec_data': spec
        })
        if result.get('success'):
            generated_files.append(output_path)
    
    # Print manual registration steps
    node_type = spec['nodeType']
    print(f"\n✅ Generated {len(generated_files)} files for {node_type} node")
    print("\n📋 Manual registration steps:")
    print(f"1. Add {node_type} to NODE_TYPE_MAP in dipeo/models/src/conversions.ts")
    print(f"2. Import and register {pascal_case(node_type)}Node in dipeo/core/static/generated_nodes.py")
    print(f"3. Add {node_type} to GraphQL schema unions in apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql")
    print(f"4. Create handler in dipeo/application/execution/handlers/{snake_case(node_type)}.py")
    print(f"5. Run 'dipeo run codegen/main --light' to regenerate the node registry")
    
    return {
        **inputs,  # Preserve all existing state
        'success': True,
        'files_generated': generated_files,
        'node_type': node_type,
        'message': f'Generated {len(generated_files)} files for {node_type} node'
    }

def initialize_codegen(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize the codegen process with empty state."""
    print("🔧 Initializing codegen...")
    print(f"🔧 Received inputs: {inputs}")
    
    # Write to a file to confirm function is called
    with open('.temp/codegen_trace.txt', 'w') as f:
        f.write(f"initialize_codegen called with: {inputs}\n")
    
    # Check for 'default' wrapper from Start node
    if 'default' in inputs and isinstance(inputs['default'], dict):
        # Unwrap the default data
        unwrapped_inputs = inputs['default']
        print(f"🔧 Unwrapped inputs from 'default': {unwrapped_inputs}")
    else:
        unwrapped_inputs = inputs
    
    return {
        **unwrapped_inputs,  # Preserve input data (unwrapped)
        'specs': [],
        'current_index': 0,
        'results': [],
        'failures': [],
        'total_files': 0
    }

def get_next_spec(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Get the next spec from the list."""
    specs = inputs.get('specs', [])
    current_index = inputs.get('current_index', 0)
    
    if current_index < len(specs):
        current_spec = specs[current_index]['node_spec']
        return {
            **inputs,
            'current_spec': current_spec,
            'raw_data': current_spec  # For generate_all compatibility
        }
    else:
        return {
            **inputs,
            'current_spec': None,
            'raw_data': None
        }

def update_progress(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Update progress after processing a spec."""
    results = inputs.get('results', [])
    failures = inputs.get('failures', [])
    total_files = inputs.get('total_files', 0)
    current_index = inputs.get('current_index', 0)
    
    # Check if generation was successful
    if inputs.get('success'):
        node_type = inputs.get('node_type', 'unknown')
        files_generated = inputs.get('files_generated', [])
        
        results.append({
            'node_type': node_type,
            'status': 'success',
            'files_count': len(files_generated)
        })
        total_files += len(files_generated)
        print(f"✅ Generated {len(files_generated)} files for {node_type}")
    else:
        # Handle validation or generation failure
        current_spec = inputs.get('current_spec', {})
        node_type = current_spec.get('nodeType', 'unknown')
        error = inputs.get('error', inputs.get('message', 'Unknown error'))
        
        failures.append({
            'node_type': node_type,
            'error': error
        })
        print(f"❌ Failed to generate {node_type}: {error}")
    
    return {
        **inputs,
        'current_index': current_index + 1,
        'results': results,
        'failures': failures,
        'total_files': total_files
    }

def generate_node_registry(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the node registry file."""
    results = inputs.get('results', [])
    
    if not results:
        return {**inputs, 'registry_error': 'No successful node generations'}
    
    # Extract node types
    node_types = []
    for result in results:
        if result.get('status') == 'success':
            node_type = result.get('node_type', '')
            if node_type:
                node_types.append({
                    'nodeType': node_type,
                    'nodeTypeCamel': camel_case(node_type),
                    'nodeTypePascal': pascal_case(node_type)
                })
    
    # Sort for consistent output
    node_types.sort(key=lambda x: x['nodeType'])
    
    # Use the node registry template
    registry_template = TEMPLATES['node_registry']
    registry_output = str(NODE_REGISTRY_PATH)
    
    result = render_template({
        'template': registry_template,
        'output_path': registry_output,
        'spec_data': {'nodes': node_types}
    })
    
    if result.get('success'):
        print(f"\n✅ Generated node registry with {len(node_types)} nodes")
        return {**inputs, 'registry_generated': True}
    else:
        return {**inputs, 'registry_error': result.get('error', 'Failed')}

def generate_summary(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary of the codegen process."""
    print(f"\n📊 Generating summary...")
    
    specs = inputs.get('specs', [])
    results = inputs.get('results', [])
    failures = inputs.get('failures', [])
    total_files = inputs.get('total_files', 0)
    
    # Write debug info to file
    debug_file = Path(".temp/codegen_debug.txt")
    with open(debug_file, 'a') as f:
        f.write(f"\n=== generate_summary called ===\n")
        f.write(f"Results: {len(results)}, Failures: {len(failures)}, Total files: {total_files}\n")
    
    # Count file types
    field_configs = len([r for r in results if r['status'] == 'success'])
    node_configs = field_configs  # Same count
    components = field_configs  # Same count
    
    summary = {
        'total_nodes': len(specs),
        'succeeded': len(results),
        'failed': len(failures),
        'total_files': total_files,
        'field_configs': field_configs,
        'node_configs': node_configs,
        'components': components,
        'results': results,
        'failures': failures,
        'summary': f"Successfully generated {len(results)} out of {len(specs)} node configurations"
    }
    
    print(f"\n📊 Summary: {summary['summary']}")
    print(f"   Total files: {total_files}")
    if failures:
        print(f"   ⚠️  Failed: {len(failures)} nodes")
    
    return summary

# Convenience functions for diagrams
def save_temp_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save data to temp file for passing between nodes."""
    data = inputs.get('data', inputs)
    filename = inputs.get('filename', 'temp_data.json')
    
    temp_file = TEMP_DIR / filename
    temp_file.write_text(json.dumps(data, indent=2))
    
    return {'saved_to': str(temp_file)}

def load_temp_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load data from temp file."""
    filename = inputs.get('filename', 'temp_data.json')
    temp_file = TEMP_DIR / filename
    
    if not temp_file.exists():
        return {'error': f'Temp file not found: {temp_file}'}
    
    return json.loads(temp_file.read_text())


def generate_all_nodes(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code for all node specifications in the specifications directory."""
    # Allow filtering by specific nodes
    node_filter = inputs.get('nodes', [])
    
    results = {
        'succeeded': [],
        'failed': [],
        'total_files': 0
    }
    
    # Find all JSON specifications
    spec_files = list(SPECS_DIR.glob('*.json'))
    
    if node_filter:
        # Filter to only requested nodes
        spec_files = [f for f in spec_files if f.stem in node_filter]
    
    print(f"\n🔍 Found {len(spec_files)} node specifications to process")
    
    for spec_file in spec_files:
        node_name = spec_file.stem
        print(f"\n📄 Processing {node_name}...")
        
        try:
            # Load the specification
            spec_data = json.loads(spec_file.read_text())
            
            # Generate all files for this node
            result = generate_all({'raw_data': spec_data})
            
            if result.get('success'):
                results['succeeded'].append({
                    'node': node_name,
                    'files': result.get('files_generated', [])
                })
                results['total_files'] += len(result.get('files_generated', []))
            else:
                results['failed'].append({
                    'node': node_name,
                    'error': result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            results['failed'].append({
                'node': node_name,
                'error': str(e)
            })
            print(f"  ❌ Error: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Batch Generation Summary:")
    print(f"  ✅ Succeeded: {len(results['succeeded'])} nodes")
    print(f"  ❌ Failed: {len(results['failed'])} nodes")
    print(f"  📁 Total files generated: {results['total_files']}")
    
    if results['failed']:
        print(f"\n❌ Failed nodes:")
        for failure in results['failed']:
            print(f"  - {failure['node']}: {failure['error']}")
    
    # Generate the node registry if we have successful nodes
    if results['succeeded']:
        print(f"\n📝 Generating node registry...")
        # Load all successful node specifications
        node_specs = []
        for spec_file in spec_files:
            if any(s['node'] == spec_file.stem for s in results['succeeded']):
                spec_data = json.loads(spec_file.read_text())
                node_specs.append(spec_data)
        
        # Convert to the expected format for generate_node_registry
        registry_inputs = {
            'results': [{'status': 'success', 'node_type': spec['nodeType']} for spec in node_specs]
        }
        registry_result = generate_node_registry(registry_inputs)
        if registry_result.get('registry_generated'):
            print(f"  ✅ Generated node registry")
            results['registry_generated'] = True
        else:
            print(f"  ❌ Failed to generate registry: {registry_result.get('registry_error', 'Unknown error')}")
            results['registry_generated'] = False
    
    return results


# Main entry point for command line usage
if __name__ == "__main__":
    # Run batch generation
    result = generate_all_nodes({})
    
    # Exit with error code if any failures
    sys.exit(len(result.get('failed', [])))