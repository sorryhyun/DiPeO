"""Prepare data for different generators by transforming model data to expected formats."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List


def prepare_zod_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for Zod schema generation.
    
    Transforms the model data from transform_ast_to_python_models
    into the format expected by the Zod generator template.
    """
    print("[prepare_zod_data] Starting preparation")
    
    # Get model data from inputs
    model_data = inputs.get('default', inputs)
    
    if not model_data or 'models' not in model_data:
        print("[prepare_zod_data] No models found in input")
        return {'error': 'No model data provided'}
    
    # The zod generator expects data in a specific format
    # We need to transform our Python-oriented model data back to TypeScript-oriented
    zod_data = {
        'models': [],
        'enums': model_data.get('enums', [])
    }
    
    # Process each model
    for model in model_data.get('models', []):
        if model['type'] == 'enum':
            # Enums are handled separately
            continue
        elif model['type'] == 'class':
            # Transform class model for Zod
            zod_model = {
                'name': model['name'],
                'type': 'class',
                'fields': model.get('fields', {}),
                'strict': True  # Make all schemas strict by default
            }
            zod_data['models'].append(zod_model)
    
    # Add enums to models for the template
    zod_data['models'].extend(model_data.get('enums', []))
    
    # Add type aliases from the original data if available
    for type_name, type_def in model_data.get('type_aliases', {}).items():
        zod_data['models'].append({
            'name': type_name,
            'type': 'type_alias',
            'definition': type_def
        })
    
    # Save the prepared data
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_dir = Path(base_dir) / '.temp' / 'codegen'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    zod_file = temp_dir / 'zod_data.json'
    with open(zod_file, 'w') as f:
        json.dump(zod_data, f, indent=2)
    
    print(f"[prepare_zod_data] Saved Zod data to {zod_file}")
    print(f"[prepare_zod_data] Prepared {len(zod_data['models'])} models")
    
    return zod_data


def prepare_conversion_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for conversion functions generation.
    
    Transforms the model data into the format expected by the conversions generator.
    """
    print("[prepare_conversion_data] Starting preparation")
    
    # Get model data from inputs
    model_data = inputs.get('default', inputs)
    
    if not model_data:
        print("[prepare_conversion_data] No model data provided")
        return {'error': 'No model data provided'}
    
    # The conversions generator expects specific structure
    conversion_data = {
        'models': model_data.get('models', []),
        'enums': model_data.get('enums', []),
        'type_aliases': model_data.get('type_aliases', {}),
        'imports': model_data.get('imports', [])
    }
    
    # Save the prepared data
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_dir = Path(base_dir) / '.temp' / 'codegen'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    conversion_file = temp_dir / 'conversion_data.json'
    with open(conversion_file, 'w') as f:
        json.dump(conversion_data, f, indent=2)
    
    print(f"[prepare_conversion_data] Saved conversion data to {conversion_file}")
    
    return conversion_data


def prepare_schema_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for JSON schema generation.
    
    Transforms the model data into the format expected by the JSON schema generator.
    """
    print("[prepare_schema_data] Starting preparation")
    
    # Get model data from inputs
    model_data = inputs.get('default', inputs)
    
    if not model_data:
        print("[prepare_schema_data] No model data provided")
        return {'error': 'No model data provided'}
    
    # Transform to schema format
    schema_data = {
        'models': [],
        'enums': model_data.get('enums', [])
    }
    
    # Process each model for JSON schema
    for model in model_data.get('models', []):
        if model['type'] == 'class':
            schema_model = {
                'name': model['name'],
                'type': 'object',
                'properties': {},
                'required': []
            }
            
            # Transform fields to JSON schema properties
            for field_name, field_info in model.get('fields', {}).items():
                schema_model['properties'][field_name] = {
                    'type': python_type_to_json_type(field_info.get('type', 'Any')),
                    'description': field_info.get('description', '')
                }
                
                if field_info.get('required', True):
                    schema_model['required'].append(field_name)
            
            schema_data['models'].append(schema_model)
    
    # Save the prepared data
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_dir = Path(base_dir) / '.temp' / 'codegen'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    schema_file = temp_dir / 'schema_data.json'
    with open(schema_file, 'w') as f:
        json.dump(schema_data, f, indent=2)
    
    print(f"[prepare_schema_data] Saved schema data to {schema_file}")
    print(f"[prepare_schema_data] Prepared {len(schema_data['models'])} models")
    
    return schema_data


def python_type_to_json_type(py_type: str) -> str:
    """Convert Python type to JSON schema type."""
    type_map = {
        'str': 'string',
        'int': 'integer',
        'float': 'number',
        'bool': 'boolean',
        'None': 'null',
        'Any': 'object',
        'Dict': 'object',
        'List': 'array'
    }
    
    # Handle complex types
    if py_type.startswith('List['):
        return 'array'
    elif py_type.startswith('Dict['):
        return 'object'
    elif py_type.startswith('Optional['):
        # Extract inner type
        inner = py_type[9:-1]
        return python_type_to_json_type(inner)
    
    return type_map.get(py_type, 'string')