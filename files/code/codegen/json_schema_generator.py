"""Generate JSON Schema from model definitions."""

import json
from typing import Any, Dict, List, Optional


def generate_json_schemas(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON Schema definitions from model data."""
    schema_data = inputs.get('schema_data', {})
    models = schema_data.get('models', [])
    
    schemas = {}
    generated_files = []
    
    for model in models:
        if model['type'] == 'class':
            schema = generate_model_schema(model)
            schemas[model['name']] = schema
            
            # Write individual schema file
            file_path = f"dipeo/models/schemas/{model['name']}.json"
            generated_files.append({
                'path': file_path,
                'type': 'json_schema',
                'content': json.dumps(schema, indent=2)
            })
    
    # Generate master schema file with all definitions
    master_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": schemas,
        "title": "DiPeO Model Schemas",
        "description": "Generated JSON Schema definitions for DiPeO models"
    }
    
    generated_files.append({
        'path': 'dipeo/models/schemas/all.json',
        'type': 'json_schema',
        'content': json.dumps(master_schema, indent=2)
    })
    
    return {
        'schemas': schemas,
        'generated_files': generated_files
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