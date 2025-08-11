"""
Strawberry GraphQL types generator for DiPeO V2.
Simplified for use with template_job node.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any


def extract_node_specs(inputs: dict) -> dict:
    """Extract node specifications from cached AST data."""
    # Get base directory
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    cache_dir = base_dir / 'temp'
    
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
                # print(f"Found {len(node_specs)} specs")
                return {'node_specs': node_specs}
        except Exception as e:
            pass
            # print(f"Error reading consolidated cache: {e}")
    
    # Get spec files from input or discover dynamically
    spec_files = inputs.get('spec_files', [])
    
    if not spec_files:
        # Discover files dynamically
        if cache_dir.exists():
            spec_files = [f.name for f in cache_dir.glob('*.spec.ts.json')]
            # print(f"Discovered {len(spec_files)} spec files")
    
    for filename in spec_files:
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Extract the node specification
                    for const in data.get('constants', []):
                        if const.get('name', '').endswith('Spec'):
                            spec_value = const.get('value', {})
                            if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                                # Clean up nodeType (remove quotes and NodeType. prefix)
                                node_type = spec_value.get('nodeType', '')
                                node_type = node_type.replace('NodeType.', '').replace('"', '').lower()
                                
                                node_specs.append({
                                    'name': node_type,
                                    'displayName': spec_value.get('displayName'),
                                    'category': spec_value.get('category'),
                                    'description': spec_value.get('description'),
                                    'fields': spec_value.get('fields', [])
                                })
            except Exception as e:
                pass
                # print(f"  Error reading {filename}: {e}")
    
    print(f"Found {len(node_specs)} specs")
    
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
        # Special handling for acronyms like 'db' that should be 'DB'
        if node_type == 'db':
            class_name = 'DB'
        else:
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
    
    # Return data that will be available in the template
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
    
    # Return data that will be available in the template
    result = {
        'mutations': mutations,
        'strawberry_types': strawberry_types,
        'generated_at': datetime.now().isoformat()
    }
    
    return result