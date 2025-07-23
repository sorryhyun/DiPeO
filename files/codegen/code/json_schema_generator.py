"""Generate JSON Schema from model definitions."""

import json
import os
from typing import Any, Dict, List, Optional


def generate_json_schemas(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON Schema definitions from model data."""
    # Read schema_data from saved file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    schema_data_file = os.path.join(temp_base, 'schema_data.json')
    
    print(f"[generate_json_schemas] Loading schema data from: {schema_data_file}")
    
    if not os.path.exists(schema_data_file):
        print(f"[generate_json_schemas] ERROR: Schema data file not found: {schema_data_file}")
        return {'error': 'Schema data file not found'}
    
    # Load the schema data
    with open(schema_data_file, 'r') as f:
        schema_data = json.load(f)
    
    models = schema_data.get('models', [])
    
    print(f"[generate_json_schemas] Processing {len(models)} models")
    
    schemas = {}
    generated_files = []
    
    for model in models:
        if model['type'] == 'class':
            schema = generate_model_schema(model)
            schemas[model['name']] = schema
            
            # Create schema directory
            schema_dir = os.path.join(temp_dir, 'dipeo', 'models', 'schemas')
            os.makedirs(schema_dir, exist_ok=True)
            
            # Write individual schema file
            file_path = os.path.join(schema_dir, f"{model['name']}.json")
            with open(file_path, 'w') as f:
                json.dump(schema, f, indent=2)
            
            generated_files.append({
                'path': file_path,
                'type': 'json_schema'
            })
    
    # Generate master schema file with all definitions
    master_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": schemas,
        "title": "DiPeO Model Schemas",
        "description": "Generated JSON Schema definitions for DiPeO models"
    }
    
    # Write master schema
    master_path = os.path.join(schema_dir, 'all.json')
    with open(master_path, 'w') as f:
        json.dump(master_schema, f, indent=2)
    
    generated_files.append({
        'path': master_path,
        'type': 'json_schema'
    })
    
    print(f"[generate_json_schemas] Generated {len(generated_files)} schema files")
    
    # Save result info to file for combine_results
    result_file = os.path.join(temp_base, 'schema_result.json')
    with open(result_file, 'w') as f:
        json.dump({'generated_files': generated_files}, f)
    
    return {
        'schemas': schemas,
        'generated_files': generated_files,
        'success': True
    }


def generate_model_schema(model: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON Schema for a single model."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": model['name'],
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
    
    if model.get('docstring'):
        schema['description'] = model['docstring']
    
    # Process fields
    for field_name, field_info in model.get('fields', {}).items():
        prop_schema = generate_property_schema(field_info)
        schema['properties'][field_name] = prop_schema
        
        if field_info.get('required', True):
            schema['required'].append(field_name)
    
    return schema


def generate_property_schema(field: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON Schema for a property."""
    prop_schema = {}
    
    # Add description if available
    if field.get('description'):
        prop_schema['description'] = field['description']
    
    # Map Python types to JSON Schema types
    python_type = field.get('type', 'Any')
    
    if 'Optional[' in python_type:
        # Extract inner type from Optional
        inner_type = python_type.replace('Optional[', '').rstrip(']')
        prop_schema = map_type_to_schema(inner_type)
        # Optional types can be null
        if 'type' in prop_schema:
            prop_schema['type'] = [prop_schema['type'], 'null']
    else:
        prop_schema.update(map_type_to_schema(python_type))
    
    # Add default value if specified
    if 'default' in field and field['default'] is not None:
        prop_schema['default'] = field['default']
    
    return prop_schema


def map_type_to_schema(python_type: str) -> Dict[str, Any]:
    """Map Python type to JSON Schema type."""
    # Basic type mappings
    type_mappings = {
        'str': {'type': 'string'},
        'int': {'type': 'integer'},
        'float': {'type': 'number'},
        'bool': {'type': 'boolean'},
        'Any': {},  # No type restriction
        'None': {'type': 'null'},
        'datetime': {'type': 'string', 'format': 'date-time'},
        'date': {'type': 'string', 'format': 'date'},
        'time': {'type': 'string', 'format': 'time'},
        'UUID': {'type': 'string', 'format': 'uuid'},
    }
    
    # Check for exact match
    if python_type in type_mappings:
        return type_mappings[python_type]
    
    # Handle List types
    if python_type.startswith('List['):
        inner_type = python_type[5:-1]
        return {
            'type': 'array',
            'items': map_type_to_schema(inner_type)
        }
    
    # Handle Dict types
    if python_type.startswith('Dict['):
        # Extract key and value types
        inner = python_type[5:-1]
        # Simple parsing - assumes no nested generics
        parts = inner.split(', ', 1)
        if len(parts) == 2:
            key_type, value_type = parts
            if key_type == 'str':
                return {
                    'type': 'object',
                    'additionalProperties': map_type_to_schema(value_type)
                }
        return {'type': 'object'}
    
    # Handle Union types
    if python_type.startswith('Union['):
        inner = python_type[6:-1]
        types = [t.strip() for t in inner.split(',')]
        schemas = [map_type_to_schema(t) for t in types]
        
        # If it's a simple union of types, use anyOf
        return {'anyOf': schemas}
    
    # Handle Literal types
    if python_type.startswith('Literal['):
        inner = python_type[8:-1]
        # Parse literal values
        values = []
        for val in inner.split(','):
            val = val.strip().strip('"\'')
            values.append(val)
        return {'enum': values}
    
    # Handle branded types (NodeID, ArrowID, etc.)
    branded_types = ['NodeID', 'ArrowID', 'PersonID', 'Handle']
    if python_type in branded_types:
        return {'type': 'string', 'pattern': '^[a-zA-Z0-9_-]+$'}
    
    # Handle enum types
    if python_type in ['NodeType', 'ExecutionStatus', 'DiagramFormat']:
        # These would need to reference the enum definition
        return {'$ref': f'#/definitions/{python_type}'}
    
    # Default to string for unknown types
    return {'type': 'string'}