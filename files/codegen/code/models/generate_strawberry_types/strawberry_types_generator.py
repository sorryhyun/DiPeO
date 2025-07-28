"""
Strawberry GraphQL types generator for DiPeO.
Generates Strawberry types from node specifications using Pydantic models.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any
from jinja2 import Template, StrictUndefined


def extract_node_specs(inputs: dict) -> dict:
    """Extract node specifications from cached AST data."""
    # Get base directory
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    cache_dir = base_dir / '.temp'
    
    node_specs = []
    
    # Check for the consolidated cache file first
    consolidated_file = cache_dir / 'all_node_specs_ast.json'
    if consolidated_file.exists():
        try:
            with open(consolidated_file, 'r') as f:
                data = json.load(f)
                # The structure is: { "node_specs": { "node_name": { "constants": [...] } } }
                if 'node_specs' in data:
                    for node_name, node_data in data['node_specs'].items():
                        if isinstance(node_data, dict) and 'constants' in node_data:
                            for const in node_data['constants']:
                                if const.get('name', '').endswith('Spec'):
                                    spec_value = const.get('value', {})
                                    if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                                        # Clean up nodeType (remove quotes and NodeType. prefix)
                                        node_type = spec_value.get('nodeType', '')
                                        node_type = node_type.replace('NodeType.', '').lower()
                                        
                                        node_specs.append({
                                            'name': node_type,
                                            'displayName': spec_value.get('displayName'),
                                            'category': spec_value.get('category'),
                                            'description': spec_value.get('description'),
                                            'fields': spec_value.get('fields', [])
                                        })
                                        print(f"  Found spec: {node_type}")
                print(f"Found {len(node_specs)} node specifications from consolidated cache")
                return {'node_specs': node_specs}
        except Exception as e:
            print(f"Error reading consolidated cache: {e}")
    
    # Fallback to individual files
    spec_files = [
        'node_spec_start_ast.json', 'node_spec_condition_ast.json', 'node_spec_person_job_ast.json',
        'node_spec_code_job_ast.json', 'node_spec_api_job_ast.json', 'node_spec_endpoint_ast.json',
        'node_spec_db_ast.json', 'node_spec_user_response_ast.json', 'node_spec_notion_ast.json',
        'node_spec_person_batch_job_ast.json', 'node_spec_hook_ast.json', 'node_spec_template_job_ast.json',
        'node_spec_json_schema_validator_ast.json', 'node_spec_typescript_ast_ast.json', 'node_spec_sub_diagram_ast.json'
    ]
    
    print(f"Looking for node spec cache files in: {cache_dir}")
    
    for filename in spec_files:
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Extract the node specification
                    for const in data.get('consts', []):
                        if const.get('name', '').endswith('Spec'):
                            spec_value = const.get('value', {})
                            if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                                node_specs.append({
                                    'name': spec_value.get('nodeType'),
                                    'displayName': spec_value.get('displayName'),
                                    'category': spec_value.get('category'),
                                    'description': spec_value.get('description'),
                                    'fields': spec_value.get('fields', [])
                                })
                                print(f"  Found spec: {spec_value.get('nodeType')}")
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
    
    print(f"Found {len(node_specs)} node specifications")
    
    return {'node_specs': node_specs}


def generate_strawberry_types(inputs: dict) -> dict:
    """Generate Strawberry GraphQL types from node specifications."""
    # Handle the double nesting from DiPeO
    node_specs_data = inputs.get('node_specs', {})
    if isinstance(node_specs_data, dict) and 'node_specs' in node_specs_data:
        # Unwrap the double nesting
        node_specs = node_specs_data['node_specs']
    else:
        node_specs = node_specs_data if isinstance(node_specs_data, list) else []
    
    # Prepare data for template
    strawberry_types = []
    
    for spec in node_specs:
        node_type = spec['name']
        # Convert node type to class name (e.g., 'person_job' -> 'PersonJob')
        class_name = ''.join(word.capitalize() for word in node_type.split('_'))
        
        # Convert to Pydantic model name (template will append "NodeData")
        pydantic_model = f"{class_name}"
        
        strawberry_types.append({
            'node_type': node_type,
            'class_name': f"{class_name}",  # Template will append "DataType"
            'pydantic_model': pydantic_model,
            'display_name': spec.get('displayName', ''),
            'description': spec.get('description', ''),
            'category': spec.get('category', '')
        })
    
    result = {
        'strawberry_types': strawberry_types,
        'generated_at': datetime.now().isoformat()
    }
    
    return result


def generate_node_mutations(inputs: dict) -> dict:
    """Generate node-specific mutations for each node type."""
    # Handle the double nesting from DiPeO
    strawberry_types_data = inputs.get('strawberry_types', {})
    if isinstance(strawberry_types_data, dict) and 'strawberry_types' in strawberry_types_data:
        # Unwrap the nesting
        strawberry_types = strawberry_types_data['strawberry_types']
    else:
        strawberry_types = strawberry_types_data if isinstance(strawberry_types_data, list) else []
    
    mutations = []
    
    for node_type_info in strawberry_types:
        # Generate create mutation
        mutations.append({
            'name': f"create_{node_type_info['node_type']}_node",
            'input_type': f"Create{node_type_info['class_name']}Input",
            'return_type': f"{node_type_info['class_name']}DataType",
            'node_type': node_type_info['node_type'],
            'operation': 'create'
        })
        
        # Generate update mutation
        mutations.append({
            'name': f"update_{node_type_info['node_type']}_node",
            'input_type': f"Update{node_type_info['class_name']}Input",
            'return_type': f"{node_type_info['class_name']}DataType",
            'node_type': node_type_info['node_type'],
            'operation': 'update'
        })
    
    result = {
        'mutations': mutations,
        'strawberry_types': strawberry_types,
        'generated_at': datetime.now().isoformat()
    }
    
    return result


def prepare_template_data(inputs: dict) -> dict:
    """Prepare template data from node generation output."""
    # This function can handle both strawberry types and mutations data
    
    # Try to get mutations data first (for mutations generation)
    mutations_data = inputs.get('mutations', {})
    if mutations_data and isinstance(mutations_data, dict):
        return mutations_data
    
    # Otherwise try strawberry types (for types generation)
    strawberry_types_data = inputs.get('strawberry_types', {})
    if strawberry_types_data and isinstance(strawberry_types_data, dict):
        return strawberry_types_data
    
    # Default fallback
    return {
        'strawberry_types': [],
        'generated_at': datetime.now().isoformat()
    }


def render_strawberry_schema(inputs: dict) -> dict:
    """Render the Strawberry GraphQL schema."""
    template_content = inputs.get('template_content', '')
    
    # Get prepared data from the 'default' connection (following GraphQL generator pattern)
    template_data = inputs.get('default', {})
    
    # Ensure we have all required keys
    if not isinstance(template_data, dict):
        template_data = {
            'strawberry_types': [],
            'generated_at': datetime.now().isoformat()
        }
    
    if 'strawberry_types' not in template_data:
        template_data['strawberry_types'] = []
    if 'generated_at' not in template_data:
        template_data['generated_at'] = datetime.now().isoformat()
    
    # Create the template
    jinja_template = Template(template_content, undefined=StrictUndefined)
    
    try:
        rendered = jinja_template.render(**template_data)
        return {'generated_code': rendered}
    except Exception as e:
        import traceback
        error_msg = f"Template rendering error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {'generated_code': error_msg}


def generate_summary(inputs: dict) -> dict:
    """Generate summary of Strawberry types generation."""
    mutations = inputs.get('mutations', [])
    strawberry_types = inputs.get('strawberry_types', [])
    
    print(f"\n=== Strawberry GraphQL Types Generation Complete ===")
    print(f"Generated {len(strawberry_types)} node types")
    print(f"Generated {len(mutations)} mutations")
    print(f"\nOutput written to: dipeo/application/graphql/types/nodes.py")
    
    return {
        'status': 'success',
        'message': 'Strawberry types generated successfully',
        'details': {
            'types_count': len(strawberry_types),
            'mutations_count': len(mutations)
        }
    }