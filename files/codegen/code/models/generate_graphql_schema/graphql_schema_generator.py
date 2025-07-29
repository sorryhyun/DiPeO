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


# ============================================================================
# Node Data AST Combination
# ============================================================================

def combine_node_data_ast(inputs):
    """Combine all node data AST files from cache."""
    # Get base directory
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    # Read all node data AST files from cache
    cache_dir = base_dir / '.temp'
    
    # Combine all interfaces, types, and enums from node data files
    all_interfaces = []
    all_types = []
    all_enums = []
    
    # List of node data cache files
    node_data_files = [
        'start_data_ast.json', 'condition_data_ast.json', 'person-job_data_ast.json',
        'code-job_data_ast.json', 'api-job_data_ast.json', 'endpoint_data_ast.json',
        'db_data_ast.json', 'user-response_data_ast.json', 'notion_data_ast.json',
        'person-batch-job_data_ast.json', 'hook_data_ast.json', 'template-job_data_ast.json',
        'json-schema-validator_data_ast.json', 'typescript-ast_data_ast.json', 'sub-diagram_data_ast.json'
    ]
    
    print(f"Looking for cache files in: {cache_dir}")
    
    for filename in node_data_files:
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    all_interfaces.extend(data.get('interfaces', []))
                    all_types.extend(data.get('types', []))
                    all_enums.extend(data.get('enums', []))
                    print(f"  Loaded {filename}: {len(data.get('interfaces', []))} interfaces")
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
        else:
            print(f"  File not found: {filename}")
    
    print(f"Combined node data: {len(all_interfaces)} interfaces, {len(all_types)} types, {len(all_enums)} enums")
    
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
    """Map TypeScript types to GraphQL types"""
    type_map = {
        'string': 'String',
        'number': 'Float', 
        'boolean': 'Boolean',
        'any': 'JSONScalar',
        'unknown': 'JSONScalar',
        'void': 'Boolean'  # GraphQL doesn't have void
    }
    
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
    
    # Check mapping
    if clean_type in type_map:
        return type_map[clean_type]
    
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
        # For GraphQL enums, use the actual values instead of member names
        values = []
        for m in enum.get('members', []):
            # Use the value if it exists, otherwise fall back to name
            value = m.get('value', m.get('name'))
            values.append(value)
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
        # Debug: print interfaces from node_data_ast
        node_interfaces = node_data_ast.get('interfaces', [])
        print(f"Node data interfaces found: {[i.get('name') for i in node_interfaces]}")
    if enums_ast:
        ast_sources.append(enums_ast)
    if integration_ast:
        ast_sources.append(integration_ast)
        # Debug: print interfaces from integration_ast
        integration_interfaces = integration_ast.get('interfaces', [])
        print(f"Integration interfaces found: {[i.get('name') for i in integration_interfaces]}")
    
    for ast in ast_sources:
        all_interfaces.extend(ast.get('interfaces', []))
        all_enums.extend(ast.get('enums', []))
        all_types.extend(ast.get('types', []))
    
    # Extract different type categories
    scalars = extract_scalars(all_types)
    enums = extract_enums(all_enums)
    
    # Extract types from interfaces
    type_results = extract_types_from_interfaces(all_interfaces, enums, scalars)
    
    print(f"Extracted:")
    print(f"  - {len(scalars)} scalars")
    print(f"  - {len(enums)} enums")
    print(f"  - {len(type_results['types'])} types")
    print(f"  - {len(type_results['input_types'])} input types")
    print(f"  - {len(type_results['node_types'])} node data types: {type_results['node_types']}")
    
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
        print(error_msg)
        # Return the error as the generated content so we can see it
        result = {'generated_code': error_msg}
    
    return result


def generate_summary(inputs):
    """Generate summary of GraphQL schema generation."""
    graphql_types = inputs.get('graphql_types', {})
    
    print(f"\n=== GraphQL Schema Generation Complete ===")
    print(f"Generated {len(graphql_types.get('scalars', []))} scalars")
    print(f"Generated {len(graphql_types.get('enums', []))} enums") 
    print(f"Generated {len(graphql_types.get('types', []))} types")
    print(f"Generated {len(graphql_types.get('input_types', []))} input types")
    print(f"\nOutput written to: dipeo/diagram_generated_staged/domain-schema.graphql")
    
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