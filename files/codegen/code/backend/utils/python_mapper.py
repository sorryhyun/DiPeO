"""Python type mapping utilities."""
from typing import Dict, Any, List, Optional


def map_to_python_type(field_type: str, ts_to_py_type: Optional[Dict[str, str]] = None) -> str:
    """Map generic field types to Python type annotations.
    
    Args:
        field_type: TypeScript type to convert
        ts_to_py_type: Optional mapping from extracted codegen-mappings.ts
    """
    # Use centralized mappings if provided
    if ts_to_py_type and field_type in ts_to_py_type:
        return ts_to_py_type[field_type]
    
    # Fallback to basic type mappings for primitive types
    basic_type_map = {
        'string': 'str',
        'text': 'str',
        'integer': 'int',
        'int': 'int',
        'number': 'int',  # Default to int, not float
        'float': 'float',
        'double': 'float',
        'boolean': 'bool',
        'bool': 'bool',
        'object': 'Dict[str, Any]',
        'dict': 'Dict[str, Any]',
        'array': 'List[Any]',
        'list': 'List[Any]',
        'any': 'Any',
        'null': 'None',
        'none': 'None',
        'date': 'datetime.date',
        'datetime': 'datetime.datetime',
        'time': 'datetime.time',
        'uuid': 'UUID',
        'bytes': 'bytes',
        'enum': 'str',  # Will be overridden if enum class exists
    }
    
    # Handle array types like string[], number[]
    if field_type.endswith('[]'):
        base_type = field_type[:-2]
        # Check centralized mappings first for array types
        if ts_to_py_type and field_type in ts_to_py_type:
            return ts_to_py_type[field_type]
        mapped_base = map_to_python_type(base_type, ts_to_py_type)
        return f"List[{mapped_base}]"
    
    # Handle generic types like List[str], Dict[str, int]
    if '[' in field_type and ']' in field_type:
        # Already a Python type annotation, return as-is
        return field_type
    
    # Handle Array<Type> or List<Type> notation
    if '<' in field_type and '>' in field_type:
        base_type = field_type.split('<')[0].lower()
        inner_type = field_type.split('<')[1].rstrip('>')
        
        if base_type in ['array', 'list']:
            return f"List[{map_to_python_type(inner_type, ts_to_py_type)}]"
        elif base_type in ['dict', 'map', 'record']:
            if ',' in inner_type:
                key_type, value_type = inner_type.split(',', 1)
                return f"Dict[{map_to_python_type(key_type.strip(), ts_to_py_type)}, {map_to_python_type(value_type.strip(), ts_to_py_type)}]"
            else:
                return f"Dict[str, {map_to_python_type(inner_type, ts_to_py_type)}]"
        elif base_type == 'optional':
            return f"Optional[{map_to_python_type(inner_type, ts_to_py_type)}]"
    
    return basic_type_map.get(field_type.lower(), field_type)


def get_python_default(field: Dict[str, Any], ts_to_py_type: Optional[Dict[str, str]] = None) -> str:
    """Get Python default value for a field."""
    if 'default' in field:
        default = field['default']
        
        # Handle different default types
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return 'True' if default else 'False'
        elif isinstance(default, (int, float)):
            return str(default)
        elif isinstance(default, list):
            return '[]'
        elif isinstance(default, dict):
            return '{}'
        elif default is None:
            return 'None'
    
    # For fields without explicit defaults
    if not field.get('required', False):
        return 'None'
    
    # Return type-based defaults for required fields with no default
    field_type = field.get('type', 'string')
    py_type = map_to_python_type(field_type, ts_to_py_type)
    
    if py_type == 'str':
        return '""'
    elif py_type in ['int', 'float']:
        return '0'
    elif py_type == 'bool':
        return 'False'
    elif py_type.startswith('List['):
        return '[]'
    elif py_type.startswith('Dict['):
        return '{}'
    else:
        return 'None'


def get_pydantic_field(field: Dict[str, Any], ts_to_py_type: Optional[Dict[str, str]] = None) -> str:
    """Generate Pydantic Field definition for a field."""
    parts = []
    
    # Default value
    default = get_python_default(field, ts_to_py_type)
    if default != 'None' or not field.get('required', False):
        parts.append(f"default={default}")
    
    # Description
    if 'description' in field:
        parts.append(f'description="{field["description"]}"')
    
    # Alias (if field name is not valid Python identifier)
    field_name = field.get('name', '')
    if '-' in field_name or field_name in ['class', 'def', 'return', 'import']:
        parts.append(f'alias="{field_name}"')
    
    # Validation constraints
    if 'min' in field:
        field_type = field.get('type', 'string')
        if field_type in ['int', 'integer', 'float', 'number']:
            parts.append(f"ge={field['min']}")
        elif field_type in ['string', 'text']:
            parts.append(f"min_length={field['min']}")
    
    if 'max' in field:
        field_type = field.get('type', 'string')
        if field_type in ['int', 'integer', 'float', 'number']:
            parts.append(f"le={field['max']}")
        elif field_type in ['string', 'text']:
            parts.append(f"max_length={field['max']}")
    
    if 'pattern' in field:
        parts.append(f'regex="{field["pattern"]}"')
    
    # Example value
    if 'example' in field:
        example = field['example']
        if isinstance(example, str):
            parts.append(f'example="{example}"')
        else:
            parts.append(f'example={example}')
    
    if parts:
        return f"Field({', '.join(parts)})"
    else:
        return "Field()"


def calculate_python_imports(spec_data: Dict[str, Any], ts_to_py_type: Optional[Dict[str, str]] = None) -> List[str]:
    """Calculate Python imports needed for the model."""
    imports = set()
    
    # Standard imports
    imports.add("from typing import Dict, Any, List, Optional, Union")
    imports.add("from pydantic import Field, BaseModel, validator")
    
    # Check field types for additional imports
    field_types = set()
    for field in spec_data.get('fields', []):
        field_type = field.get('type', 'string')
        py_type = map_to_python_type(field_type, ts_to_py_type)
        field_types.add(py_type)
    
    # Add imports based on types
    if any('datetime' in t for t in field_types):
        imports.add("from datetime import datetime, date, time")
    
    if any('UUID' in t for t in field_types):
        imports.add("from uuid import UUID")
    
    if any('Enum' in t for t in field_types):
        imports.add("from enum import Enum")
    
    # Add base node import
    imports.add("from dipeo.core.models import BaseNode")
    
    return sorted(list(imports))


def pythonize_name(name: str) -> str:
    """Convert a name to valid Python identifier."""
    # Replace invalid characters
    name = name.replace('-', '_').replace(' ', '_')
    
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"field_{name}"
    
    # Avoid Python keywords
    keywords = {'class', 'def', 'return', 'import', 'from', 'as', 'if', 'else', 
                'elif', 'while', 'for', 'in', 'and', 'or', 'not', 'is', 'None',
                'True', 'False', 'try', 'except', 'finally', 'with', 'yield',
                'lambda', 'pass', 'break', 'continue', 'global', 'nonlocal'}
    
    if name in keywords:
        name = f"{name}_field"
    
    return name