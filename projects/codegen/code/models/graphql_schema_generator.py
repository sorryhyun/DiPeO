"""
GraphQL schema generator for DiPeO.
Consolidates all GraphQL schema generation logic into a single module.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any
from jinja2 import Template, StrictUndefined

# Import type transformer from infrastructure
import sys
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
from dipeo.infrastructure.codegen.parsers.typescript.type_transformer import map_ts_type_to_python


# ============================================================================
# Node Data AST Combination
# ============================================================================

def combine_node_data_ast(inputs):
    """Combine all node data AST files from cache."""
    # Get base directory
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    # Read all node data AST files from cache
    cache_dir = base_dir / 'temp'
    
    # Import file locking for safe concurrent access
    try:
        from dipeo.infrastructure.shared.drivers.utils import get_cache_lock_manager
        cache_lock = get_cache_lock_manager(cache_dir)
    except ImportError:
        # Fallback if file locking not available
        cache_lock = None
    
    # Combine all interfaces, types, and enums from node data files
    all_interfaces = []
    all_types = []
    all_enums = []
    
    # Get node data files from input or discover dynamically
    node_data_files = inputs.get('node_data_files', [])
    
    if not node_data_files:
        # Fallback: discover files dynamically
        if cache_dir.exists():
            node_data_files = [f.name for f in cache_dir.glob('*_data_ast.json')]
            # print(f"Discovered {len(node_data_files)} node data files")
    
    # Look for cache files
    
    for filename in node_data_files:
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                if cache_lock:
                    # Use file locking for safe concurrent access
                    with cache_lock.read(file_path) as f:
                        if f:
                            data = json.load(f)
                            all_interfaces.extend(data.get('interfaces', []))
                            all_types.extend(data.get('types', []))
                            all_enums.extend(data.get('enums', []))
                else:
                    # Fallback to direct file access
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_interfaces.extend(data.get('interfaces', []))
                        all_types.extend(data.get('types', []))
                        all_enums.extend(data.get('enums', []))
                pass  # File loaded
            except Exception as e:
                pass  # Error handled
        else:
            pass  # File not found
    
    # Data combined successfully
    
    result = {
        'interfaces': all_interfaces,
        'types': all_types,
        'enums': all_enums
    }
    
    return result


# ============================================================================
# Type Conversion and Extraction
# ============================================================================

def ts_to_graphql_type(ts_type: str, enums: list, scalars: list, missing_enums: set) -> str:
    """Map TypeScript types to GraphQL types using centralized type mapping"""
    
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Handle literal string types (e.g., 'person', "json", etc.)
    if (clean_type.startswith("'") and clean_type.endswith("'")) or \
       (clean_type.startswith('"') and clean_type.endswith('"')):
        return 'String'
    
    # Handle empty object notation {} as JSONScalar
    if clean_type == '{}':
        return 'JSONScalar'
    
    # Handle complex object types (inline object definitions)
    if clean_type.startswith('{') and clean_type.endswith('}'):
        return 'JSONScalar'
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        return 'JSONScalar'
    
    # Handle arrays
    if clean_type.endswith('[]'):
        inner_type = clean_type[:-2]
        return f"[{ts_to_graphql_type(inner_type, enums, scalars, missing_enums)}]"
    
    # Handle union types with string literals
    if ' | ' in clean_type:
        parts = [part.strip() for part in clean_type.split(' | ')]
        # Check if all parts are string literals
        if all((part.startswith('"') and part.endswith('"')) or 
               (part.startswith("'") and part.endswith("'")) for part in parts):
            return 'String'  # String literal union -> String
        # Check if it's a mix of types
        return 'String'  # Fallback to String for any union
    
    # Use infrastructure's type transformer for consistency
    python_type = map_ts_type_to_python(clean_type)
    
    # Map Python types to GraphQL types
    python_to_graphql = {
        'str': 'String',
        'float': 'Float',
        'int': 'Int',
        'bool': 'Boolean',
        'Any': 'JSONScalar',
        'Dict[str, Any]': 'JSONScalar',
        'datetime': 'DateTime',
        'None': 'Boolean'  # GraphQL doesn't have void/null as type
    }
    
    # Check Python type mappings
    for py_type, gql_type in python_to_graphql.items():
        if py_type in python_type:
            return gql_type
    
    # Check if List type
    if python_type.startswith('List['):
        inner = python_type[5:-1]
        # Map inner type recursively
        inner_gql = 'JSONScalar'  # Default for complex types
        for py_type, gql_type in python_to_graphql.items():
            if py_type in inner:
                inner_gql = gql_type
                break
        return f"[{inner_gql}]"
    
    # Check if it's a known type/enum/scalar
    if any(e['name'] == clean_type for e in enums):
        return clean_type
    if any(s['name'] == clean_type for s in scalars):
        return clean_type
    
    # Track missing enums
    if clean_type and not clean_type.startswith('(') and clean_type not in ['JSONScalar']:
        missing_enums.add(clean_type)
    
    # Default to the type name (assume it's defined elsewhere)
    return clean_type


def extract_scalars(all_types: list) -> list:
    """Extract scalars (branded types ending with ID)"""
    scalars = []
    for type_alias in all_types:
        name = type_alias.get('name', '')
        if name.endswith('ID'):
            scalars.append({
                'name': name,
                'description': type_alias.get('jsDoc', '')
            })
    return scalars


def extract_enums(all_enums: list) -> list:
    """Extract enums, skipping internal ones"""
    enums = []
    for enum in all_enums:
        # Skip internal enums
        if enum.get('name', '').startswith('_'):
            continue
        # For GraphQL enums, we need the member names (not values)
        # GraphQL uses enum member names (e.g., RAW_TEXT) not values (e.g., 'raw_text')
        values = []
        for m in enum.get('members', []):
            # Use the member name for GraphQL enum values
            values.append(m.get('name'))
        enums.append({
            'name': enum.get('name'),
            'values': values
        })
    return enums


def extract_types_from_interfaces(all_interfaces: list, enums: list, scalars: list) -> dict:
    """Extract types from interfaces"""
    types = []
    input_types = []
    node_types = []
    missing_enums = set()
    
    # Add JSONScalar to scalars if not present
    if not any(s['name'] == 'JSONScalar' for s in scalars):
        scalars.append({
            'name': 'JSONScalar',
            'description': 'Arbitrary JSON value'
        })
    
    for interface in all_interfaces:
        name = interface.get('name', '')
        
        # Skip internal interfaces
        if name.startswith('_'):
            continue
        
        # Determine if it's an input type
        is_input = 'Input' in name or 'Create' in name or 'Update' in name
        
        # Track node data types
        if 'NodeData' in name and not name.startswith('_'):
            node_types.append(name)
        
        fields = []
        for prop in interface.get('properties', []):
            field_name = prop.get('name')
            field_type = prop.get('type', 'String')
            is_optional = prop.get('optional', False)
            
            # Skip internal fields
            if field_name.startswith('_'):
                continue
            
            # Convert field type
            graphql_type = ts_to_graphql_type(field_type, enums, scalars, missing_enums)
            
            # Special handling for specific problematic fields
            if field_type.startswith('Record<string,'):
                graphql_type = 'JSONScalar'
            elif field_type == '{}':
                graphql_type = 'JSONScalar'
            
            fields.append({
                'name': field_name,
                'type': graphql_type,
                'required': not is_optional,
                'default': 'null' if is_optional else None
            })
        
        type_def = {
            'name': name,
            'fields': fields,
            'description': interface.get('jsDoc', '')
        }
        
        if is_input:
            input_types.append(type_def)
        else:
            types.append(type_def)
    
    return {
        'types': types,
        'input_types': input_types,
        'node_types': node_types
    }


def extract_graphql_types_core(diagram_ast: dict, execution_ast: dict, conversation_ast: dict, 
                               node_data_ast: dict = None, enums_ast: dict = None, 
                               integration_ast: dict = None) -> dict:
    """Extract all GraphQL types from combined AST data"""
    # Combine all AST data
    all_interfaces = []
    all_enums = []
    all_types = []
    
    # Include all AST sources, including node_data_ast, enums_ast, and integration_ast if provided
    ast_sources = [diagram_ast, execution_ast, conversation_ast]
    if node_data_ast:
        ast_sources.append(node_data_ast)
        # Process node data interfaces
        node_interfaces = node_data_ast.get('interfaces', [])
    if enums_ast:
        ast_sources.append(enums_ast)
    if integration_ast:
        ast_sources.append(integration_ast)
        # Process integration interfaces
        integration_interfaces = integration_ast.get('interfaces', [])
    
    for ast in ast_sources:
        all_interfaces.extend(ast.get('interfaces', []))
        all_enums.extend(ast.get('enums', []))
        all_types.extend(ast.get('types', []))
    
    # Extract different type categories
    scalars = extract_scalars(all_types)
    enums = extract_enums(all_enums)
    
    # Extract types from interfaces
    type_results = extract_types_from_interfaces(all_interfaces, enums, scalars)
    
    # Extraction complete
    # print(f"  - {len(type_results['types'])} types")
    # print(f"  - {len(type_results['input_types'])} input types")
    # print(f"  - {len(type_results['node_types'])} node data types: {type_results['node_types']}")
    
    # Add JSONScalar if not already in scalars
    if not any(s['name'] == 'JSONScalar' for s in scalars):
        scalars.append({
            'name': 'JSONScalar',
            'description': 'Arbitrary JSON value'
        })
    
    return {
        'scalars': scalars,
        'enums': enums,
        'types': type_results['types'],
        'input_types': type_results['input_types'],
        'node_types': type_results['node_types']
    }


# ============================================================================
# Main Functions (called by diagram nodes)
# ============================================================================

def extract_graphql_types(inputs: dict) -> dict:
    """Main entry point for GraphQL types extraction"""
    diagram_ast = inputs.get('diagram_ast', {})
    execution_ast = inputs.get('execution_ast', {})
    conversation_ast = inputs.get('conversation_ast', {})
    node_data_ast = inputs.get('node_data_ast', {})
    enums_ast = inputs.get('enums_ast', {})
    integration_ast = inputs.get('integration_ast', {})
    
    return extract_graphql_types_core(diagram_ast, execution_ast, conversation_ast, 
                                      node_data_ast, enums_ast, integration_ast)


def prepare_template_data(inputs):
    """Prepare GraphQL template data for rendering."""
    graphql_types = inputs.get('graphql_types', {})
    
    # Prepare the template data
    template_data = {
        'scalars': graphql_types.get('scalars', []),
        'enums': graphql_types.get('enums', []),
        'types': graphql_types.get('types', []),
        'input_types': graphql_types.get('input_types', []),
        'node_types': graphql_types.get('node_types', []),
        'now': datetime.now().isoformat()
    }
    
    return template_data


def render_graphql_schema(inputs):
    """Render GraphQL schema using template."""
    # Get template content - it comes as a direct string input
    template_content = inputs.get('template_content', '')
    
    # Get prepared data - it comes from the 'default' connection
    template_data = inputs.get('default', {})
    
    # Ensure all expected keys exist with proper defaults
    template_context = {
        'scalars': template_data.get('scalars', []),
        'enums': template_data.get('enums', []),
        'types': template_data.get('types', []),
        'input_types': template_data.get('input_types', []),
        'node_types': template_data.get('node_types', []),
        'now': template_data.get('now', datetime.now().isoformat())
    }
    
    # Render template with error handling
    try:
        jinja_template = Template(template_content, undefined=StrictUndefined)
        rendered = jinja_template.render(**template_context)
        # Return the rendered content as 'generated_code' for DB node
        result = {'generated_code': rendered}
    except Exception as e:
        import traceback
        error_msg = f"Template rendering error: {str(e)}\n{traceback.format_exc()}"
        # print(error_msg)
        # Return the error as the generated content so we can see it
        result = {'generated_code': error_msg}
    
    return result


def generate_summary(inputs):
    """Generate summary of GraphQL schema generation."""
    import json
    
    # The connection is labeled 'graphql_data' in the diagram
    graphql_types = inputs.get('graphql_data', inputs.get('graphql_types', inputs.get('default', {})))
    
    # Handle case where graphql_types might be a JSON string
    if isinstance(graphql_types, str):
        try:
            graphql_types = json.loads(graphql_types)
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, return an error-like result
            return {
                'status': 'error',
                'message': 'GraphQL types data is not in expected format',
                'details': {
                    'scalars_count': 0,
                    'enums_count': 0,
                    'types_count': 0,
                    'input_types_count': 0
                }
            }
    
    # Ensure graphql_types is a dictionary
    if not isinstance(graphql_types, dict):
        graphql_types = {}
    
    result = {
        'status': 'success',
        'message': 'GraphQL schema generated successfully',
        'details': {
            'scalars_count': len(graphql_types.get('scalars', [])),
            'enums_count': len(graphql_types.get('enums', [])),
            'types_count': len(graphql_types.get('types', [])),
            'input_types_count': len(graphql_types.get('input_types', []))
        }
    }
    
    return result


# Backward compatibility aliases
main = extract_graphql_types


def prepare_graphql_data_for_template(inputs: dict) -> dict:
    """Prepare GraphQL data for template_job rendering.
    
    This function extracts GraphQL types and prepares them in the format
    expected by the GraphQL schema Jinja2 template.
    """
    # When DB node returns multi-file read with DataOutput, it comes wrapped in 'default'
    if 'default' in inputs and isinstance(inputs['default'], dict):
        # This is the actual file dictionary from multi-file DB read
        all_files = inputs['default']
    elif 'all_ast_files' in inputs:
        # Legacy labeled connection support
        all_files = inputs['all_ast_files']
    else:
        # Try to use inputs directly as the file dictionary
        # DB node with multiple source_details returns a dict of filepath -> content
        all_files = inputs
    
    # Extract GraphQL types from the files
    graphql_types = extract_graphql_types_from_multi_read({'all_ast_files': all_files})
    
    # Add current timestamp for the template
    graphql_types['now'] = datetime.now().isoformat()
    
    # Return the data ready for template rendering
    return graphql_types


def extract_graphql_types_from_multi_read(inputs: dict) -> dict:
    """Extract GraphQL types from multiple file read with serialize_json=true"""
    import json
    
    # Get the multiple file read output
    all_files = inputs.get('all_ast_files', {})
    
    # Parse individual AST files from the multi-read dictionary
    ast_data = {}
    node_data_interfaces = []
    node_data_types = []
    node_data_enums = []
    
    for filepath, content in all_files.items():
        if filepath.endswith('.ts.json'):
            # Extract key name from filepath (e.g., "temp/diagram.ts.json" -> "diagram")
            filename = filepath.split('/')[-1].replace('.ts.json', '')
            # Content is already parsed if serialize_json=true
            parsed_content = content if isinstance(content, dict) else json.loads(content)
            
            # Special handling for node data files
            if '.data' in filename:
                # Accumulate node data interfaces/types/enums
                node_data_interfaces.extend(parsed_content.get('interfaces', []))
                node_data_types.extend(parsed_content.get('types', []))
                node_data_enums.extend(parsed_content.get('enums', []))
            else:
                # Map regular files to expected keys
                if filename == 'diagram':
                    ast_data['diagram_ast'] = parsed_content
                elif filename == 'execution':
                    ast_data['execution_ast'] = parsed_content
                elif filename == 'conversation':
                    ast_data['conversation_ast'] = parsed_content
                elif filename == 'enums':
                    ast_data['enums_ast'] = parsed_content
                elif filename == 'integration':
                    ast_data['integration_ast'] = parsed_content
    
    # Combine all node data into a single structure
    combined_node_data = {
        'interfaces': node_data_interfaces,
        'types': node_data_types,
        'enums': node_data_enums
    } if node_data_interfaces or node_data_types or node_data_enums else {}
    
    # Call the core extraction function
    return extract_graphql_types_core(
        diagram_ast=ast_data.get('diagram_ast', {}),
        execution_ast=ast_data.get('execution_ast', {}),
        conversation_ast=ast_data.get('conversation_ast', {}),
        node_data_ast=combined_node_data,
        enums_ast=ast_data.get('enums_ast', {}),
        integration_ast=ast_data.get('integration_ast', {})
    )