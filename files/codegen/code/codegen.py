"""
Simplified codegen module - replaces complex multi-file structure.

Core functionality:
1. Load node specification JSON
2. Render Jinja2 templates  
3. Write output files
4. Print manual registration steps
"""

import json
import re
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
# Emoji to icon mapping
EMOJI_TO_ICON_MAP = {
    "🤖": "Bot",
    "🔧": "Wrench",
    "📝": "FileText",
    "🔀": "GitBranch",
    "🔄": "RefreshCw",
    "📊": "BarChart",
    "🚀": "Rocket",
    "⚡": "Zap",
    "📦": "Package",
    "🔑": "Key",
    "💾": "Save",
    "🌐": "Globe",
    "🔍": "Search",
    "⚙️": "Settings",
    "📨": "Send",
    "📥": "Download",
    "📤": "Upload",
    "🏁": "Flag",
    "🎯": "Target",
    "💡": "Lightbulb",
    "🔗": "Link",
    "🔒": "Lock",
    "🔓": "Unlock",
    "📁": "Folder",
    "📂": "FolderOpen",
}

def emoji_to_icon_name(emoji: str) -> str:
    """Convert emoji to Lucide React icon name."""
    return EMOJI_TO_ICON_MAP.get(emoji, "Activity")

# Base paths
BASE_DIR = Path.cwd()
TEMPLATE_DIR = BASE_DIR / "files/codegen/templates"
SPEC_DIR = BASE_DIR / "files/codegen/specifications/nodes"
TEMP_DIR = BASE_DIR / ".temp/codegen"

# Ensure temp dir exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Case conversion utilities
def snake_case(text: str) -> str:
    """Convert to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str(text))
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def camel_case(text: str) -> str:
    """Convert to camelCase."""
    words = re.split(r'[\s_\-]+', str(text))
    if not words:
        return ''
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])

def pascal_case(text: str) -> str:
    """Convert to PascalCase."""
    words = re.split(r'[\s_\-]+', str(text))
    return ''.join(w.capitalize() for w in words)

# Type conversion filters
def typescript_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to TypeScript type."""
    type_map = {
        'string': 'string',
        'number': 'number',
        'boolean': 'boolean',
        'select': 'string',
        'multiselect': 'string[]',
        'json': 'any',
        'array': 'any[]',
        'object': 'Record<string, any>'
    }
    return type_map.get(field.get('type', 'string'), 'any')

def python_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to Python type hint."""
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'select': 'str',
        'multiselect': 'List[str]',
        'json': 'Dict[str, Any]',
        'array': 'List[Any]',
        'object': 'Dict[str, Any]'
    }
    
    py_type = type_map.get(field.get('type', 'string'), 'Any')
    
    # Handle arrays
    if field.get('array', False) and not py_type.startswith('List'):
        py_type = f'List[{py_type}]'
    
    # Handle optional
    if not field.get('required', False):
        py_type = f'Optional[{py_type}]'
    
    return py_type

def python_default_filter(field: Dict[str, Any]) -> str:
    """Generate Python default value based on field type."""
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return str(default)
        else:
            return json.dumps(default)
    
    # Return None for optional fields
    if not field.get('required', False):
        return 'None'
    
    # No default for required fields
    return ''

def graphql_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to GraphQL type."""
    type_map = {
        'string': 'String',
        'number': 'Float',
        'boolean': 'Boolean',
        'select': 'String',
        'multiselect': '[String!]',
        'json': 'JSON',
        'array': '[JSON!]',
        'object': 'JSON'
    }
    
    graphql_type = type_map.get(field.get('type', 'string'), 'String')
    
    # Handle arrays
    if field.get('array', False):
        graphql_type = f'[{graphql_type}!]'
    
    return graphql_type

def zod_schema_filter(field: Dict[str, Any]) -> str:
    """Convert field to Zod schema."""
    field_type = field.get('type', 'string')
    required = field.get('required', False)
    
    # Build base schema
    if field_type == 'string':
        schema = "z.string()"
    elif field_type == 'number':
        schema = "z.number()"
    elif field_type == 'boolean':
        schema = "z.boolean()"
    elif field_type == 'select':
        options = field.get('options', [])
        if options:
            option_values = [f'"{opt["value"]}"' for opt in options]
            schema = f"z.enum([{', '.join(option_values)}])"
        else:
            schema = "z.string()"
    elif field_type == 'multiselect':
        schema = "z.array(z.string())"
    elif field_type == 'json':
        schema = "z.any()"
    elif field_type == 'array':
        schema = "z.array(z.any())"
    elif field_type == 'object':
        schema = "z.record(z.any())"
    else:
        schema = "z.any()"
    
    # Add optional if not required
    if not required:
        schema += ".optional()"
    
    # Add default if provided
    if 'default' in field:
        default_val = field['default']
        if isinstance(default_val, str):
            schema += f'.default("{default_val}")'
        else:
            schema += f'.default({json.dumps(default_val)})'
    
    return schema

def default_value_filter(field: Dict[str, Any]) -> str:
    """Generate default value based on field type."""
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return str(default).lower()
        else:
            return json.dumps(default)
    
    # Generate default based on type
    type_defaults = {
        'string': '""',
        'number': '0',
        'boolean': 'false',
        'select': '""',
        'multiselect': '[]',
        'json': '{}',
        'array': '[]',
        'object': '{}'
    }
    
    return type_defaults.get(field.get('type', 'string'), 'null')

def humanize_filter(text: str) -> str:
    """Convert snake_case or camelCase to human readable format."""
    # Handle snake_case
    if '_' in text:
        return ' '.join(word.capitalize() for word in text.split('_'))
    
    # Handle camelCase
    result = re.sub('([a-z])([A-Z])', r'\1 \2', str(text))
    return result[0].upper() + result[1:] if result else ''

# Main functions
def load_node_spec(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load node specification from JSON file."""
    spec_path = inputs.get('node_spec_path', '')
    if not spec_path:
        return {'error': 'No node_spec_path provided'}
    
    spec_file = Path(spec_path)
    if not spec_file.exists():
        # Try relative to spec dir
        spec_file = SPEC_DIR / spec_path
        if not spec_file.suffix:
            spec_file = spec_file.with_suffix('.json')
    
    if not spec_file.exists():
        return {'error': f'Spec file not found: {spec_file}'}
    
    return json.loads(spec_file.read_text())

def parse_spec_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse spec data and add output paths."""
    spec = inputs.get('raw_data', inputs)
    if isinstance(spec, str):
        spec = json.loads(spec)
    
    node_type = spec.get('nodeType', '')
    if not node_type:
        return {'error': 'No nodeType in spec'}
    
    # Add output paths
    spec['output_paths'] = {
        'typescript_model': f'dipeo/models/src/nodes/{node_type}Node.ts',
        'graphql_schema': f'apps/server/src/dipeo_server/api/graphql/schema/nodes/{snake_case(node_type)}_node.graphql',
        'react_component': f'apps/web/src/__generated__/nodes/{node_type}NodeForm.tsx',
        'node_config': f'apps/web/src/__generated__/nodes/{node_type}NodeConfig.ts',
        'field_config': f'apps/web/src/__generated__/fields/{node_type}FieldConfigs.ts',
        'static_node': f'dipeo/core/static/nodes/{snake_case(node_type)}_node.py'
    }
    
    # Add case variations for templates
    spec['nodeTypeSnake'] = snake_case(node_type)
    spec['nodeTypeCamel'] = camel_case(node_type)
    spec['nodeTypePascal'] = pascal_case(node_type)
    
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
    
    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Case conversion filters
    env.filters['camelCase'] = camel_case
    env.filters['PascalCase'] = pascal_case
    env.filters['snake_case'] = snake_case
    
    # Type conversion filters
    env.filters['typescript_type'] = typescript_type_filter
    env.filters['python_type'] = python_type_filter
    env.filters['python_default'] = python_default_filter
    env.filters['graphql_type'] = graphql_type_filter
    env.filters['zod_schema'] = zod_schema_filter
    env.filters['default_value'] = default_value_filter
    
    # Utility filters
    env.filters['humanize'] = humanize_filter
    env.filters['quote'] = lambda s: f'"{s}"'
    env.filters['emoji_to_icon'] = emoji_to_icon_name
    
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
        return spec
    
    templates = [
        ('frontend/typescript_model.j2', spec['output_paths']['typescript_model']),
        ('backend/graphql_schema.j2', spec['output_paths']['graphql_schema']),
        ('frontend/react_component.j2', spec['output_paths']['react_component']),
        ('frontend/node_config.j2', spec['output_paths']['node_config']),
        ('frontend/field_config.j2', spec['output_paths']['field_config']),
        ('backend/static_nodes.j2', spec['output_paths']['static_node'])
    ]
    
    generated_files = []
    for template, output_path in templates:
        result = render_template({
            'template': template,
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
    print(f"4. Register node config in apps/web/src/features/diagram/config/nodeRegistry.ts")
    print(f"5. Create handler in dipeo/application/execution/handlers/{snake_case(node_type)}.py")
    
    return {
        'success': True,
        'files_generated': generated_files,
        'node_type': node_type,
        'message': f'Generated {len(generated_files)} files for {node_type} node'
    }

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
    spec_files = list(SPEC_DIR.glob('*.json'))
    
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
    
    return results