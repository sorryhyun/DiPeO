"""Transform TypeScript AST to Python model data structure."""

from typing import Dict, Any, List, Set
import re


def transform_ast_to_python_models(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform TypeScript AST data to Python model structure expected by templates.
    
    Converts interfaces/types/enums/classes from AST into the format:
    - imports: List of import statements needed
    - models: List of model definitions (classes and enums)
    - type_aliases: Dict of type alias definitions
    """
    print("[transform_ast_to_python_models] Starting transformation")
    
    # Get AST data from inputs - check various locations
    ast_data = inputs.get('ast', {})
    if not ast_data and 'default' in inputs:
        ast_data = inputs['default']
    
    # Extract components
    interfaces = ast_data.get('interfaces', [])
    types = ast_data.get('types', [])
    enums = ast_data.get('enums', [])
    classes = ast_data.get('classes', [])
    
    print(f"[transform_ast_to_python_models] Found: {len(interfaces)} interfaces, {len(types)} types, {len(enums)} enums, {len(classes)} classes")
    
    # Initialize result structure
    result = {
        'imports': [],
        'models': [],
        'type_aliases': {},
        'enums': []  # Keep enums separate for template
    }
    
    # Track required imports
    required_imports = {
        'typing': set(),
        'enum': set(),
        'datetime': set(),
        'pydantic': set(),
        'dipeo.models': set()
    }
    
    # Add base imports
    required_imports['pydantic'].add('BaseModel')
    required_imports['pydantic'].add('Field')
    
    # Process type aliases
    for type_def in types:
        type_name = type_def.get('name', '')
        type_value = type_def.get('type', 'Any')
        
        # Handle branded types specially - they should be imported, not redefined
        if ' & ' in type_value and '__brand' in type_value:
            # These are already defined in dipeo.models, just import them
            required_imports['dipeo.models'].add(type_name)
            continue
        
        # Transform TypeScript type to Python
        python_type = transform_ts_type_to_python(type_value, required_imports)
        result['type_aliases'][type_name] = python_type
    
    # Process enums
    for enum_def in enums:
        enum_model = {
            'name': enum_def.get('name', ''),
            'type': 'enum',
            'bases': ['str', 'Enum'],
            'enum_values': []
        }
        
        # Add enum members
        for member in enum_def.get('members', []):
            member_name = member.get('name', '')
            member_value = member.get('value', member_name)
            enum_model['enum_values'].append((member_name, member_value))
        
        result['models'].append(enum_model)
        result['enums'].append(enum_model)
        required_imports['enum'].add('Enum')
    
    # Process interfaces and classes
    all_definitions = interfaces + classes
    for definition in all_definitions:
        class_model = {
            'name': definition.get('name', ''),
            'type': 'class',
            'bases': ['BaseModel'],
            'fields': {},
            'methods': []
        }
        
        # Process properties/fields
        for prop in definition.get('properties', []):
            field_name = prop.get('name', '')
            field_type = prop.get('type', 'Any')
            is_optional = prop.get('optional', False)
            
            # Transform type
            python_type = transform_ts_type_to_python(field_type, required_imports)
            
            # Create field definition
            field_def = {
                'name': field_name,
                'type': python_type,
                'required': not is_optional,
                'field_definition': None
            }
            
            # Add Field() for optional fields or fields with defaults
            if is_optional:
                # Don't add Optional wrapper if the type already has Optional
                if not python_type.startswith('Optional['):
                    field_def['field_definition'] = 'Field(default=None)'
                    required_imports['typing'].add('Optional')
                else:
                    field_def['field_definition'] = 'Field(default=None)'
            
            class_model['fields'][field_name] = field_def
        
        result['models'].append(class_model)
    
    # Build import statements
    import_statements = []
    
    # Standard library imports
    if required_imports['typing']:
        items = sorted(list(required_imports['typing']))
        import_statements.append({
            'module': 'typing',
            'items': items,
            'is_type_import': True
        })
    
    if required_imports['enum']:
        import_statements.append({
            'module': 'enum',
            'items': sorted(list(required_imports['enum'])),
            'is_type_import': False
        })
    
    if required_imports['datetime']:
        import_statements.append({
            'module': 'datetime',
            'items': sorted(list(required_imports['datetime'])),
            'is_type_import': False
        })
    
    # Third-party imports
    if required_imports['pydantic']:
        import_statements.append({
            'module': 'pydantic',
            'items': sorted(list(required_imports['pydantic'])),
            'is_type_import': False
        })
    
    # Local imports
    if required_imports['dipeo.models']:
        import_statements.append({
            'module': 'dipeo.models',
            'items': sorted(list(required_imports['dipeo.models'])),
            'is_type_import': True
        })
    
    result['imports'] = import_statements
    
    print(f"[transform_ast_to_python_models] Generated {len(result['models'])} models with {len(import_statements)} import groups")
    
    # Save the transformed data for the generators to use
    try:
        from ..utils.file_utils import save_result_info
        print("[transform_ast_to_python_models] Import successful")
    except ImportError as e:
        print(f"[transform_ast_to_python_models] Import error: {e}")
    
    import json
    from pathlib import Path
    import os
    
    # Get base directory from environment or use current working directory
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    
    # Save to model data file with absolute path
    model_data_file = Path(base_dir) / '.temp' / 'codegen' / 'model_data.json'
    print(f"[transform_ast_to_python_models] Attempting to save to: {model_data_file}")
    print(f"[transform_ast_to_python_models] Base dir: {base_dir}")
    
    try:
        model_data_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_data_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"[transform_ast_to_python_models] Successfully saved model data to {model_data_file}")
    except Exception as e:
        print(f"[transform_ast_to_python_models] Error saving model data: {e}")
    
    return result


def transform_ts_type_to_python(ts_type: str, required_imports: Dict[str, Set[str]]) -> str:
    """Transform TypeScript type to Python type."""
    # Handle null/undefined
    if ts_type in ('null', 'undefined', 'void'):
        return 'None'
    
    # Handle branded types (e.g., string & { readonly __brand: 'NodeID'; })
    if ' & ' in ts_type and '__brand' in ts_type:
        # Extract the brand name
        import re
        brand_match = re.search(r"__brand:\s*['\"]([^'\"]+)['\"]", ts_type)
        if brand_match:
            brand_name = brand_match.group(1)
            # These are NewType aliases in Python
            required_imports['typing'].add('NewType')
            return f"NewType('{brand_name}', str)"
    
    # Basic type mappings
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'any': 'Any',
        'unknown': 'Any',
        'object': 'Dict[str, Any]',
        '{}': 'Dict[str, Any]'
    }
    
    # Check basic types
    if ts_type in type_map:
        if ts_type in ('any', 'unknown'):
            required_imports['typing'].add('Any')
        if ts_type in ('object', '{}'):
            required_imports['typing'].add('Dict')
            required_imports['typing'].add('Any')
        return type_map[ts_type]
    
    # Handle Record<K, V> types
    if ts_type.startswith('Record<') and ts_type.endswith('>'):
        inner = ts_type[7:-1]
        parts = inner.split(', ', 1)
        if len(parts) == 2:
            # Record types become Dict in Python
            key_type = transform_ts_type_to_python(parts[0], required_imports)
            value_type = transform_ts_type_to_python(parts[1], required_imports)
            required_imports['typing'].add('Dict')
            return f'Dict[{key_type}, {value_type}]'
        # Fallback for simple Record
        required_imports['typing'].add('Dict')
        required_imports['typing'].add('Any')
        return 'Dict[str, Any]'
    
    # Handle arrays
    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        python_inner = transform_ts_type_to_python(inner_type, required_imports)
        required_imports['typing'].add('List')
        return f'List[{python_inner}]'
    
    # Handle Array<T>
    if ts_type.startswith('Array<') and ts_type.endswith('>'):
        inner_type = ts_type[6:-1]
        python_inner = transform_ts_type_to_python(inner_type, required_imports)
        required_imports['typing'].add('List')
        return f'List[{python_inner}]'
    
    # Handle Map<K, V>
    if ts_type.startswith('Map<') and ts_type.endswith('>'):
        inner = ts_type[4:-1]
        parts = inner.split(', ', 1)
        if len(parts) == 2:
            key_type = transform_ts_type_to_python(parts[0], required_imports)
            value_type = transform_ts_type_to_python(parts[1], required_imports)
            required_imports['typing'].add('Dict')
            return f'Dict[{key_type}, {value_type}]'
    
    # Handle Set<T>
    if ts_type.startswith('Set<') and ts_type.endswith('>'):
        inner_type = ts_type[4:-1]
        python_inner = transform_ts_type_to_python(inner_type, required_imports)
        required_imports['typing'].add('Set')
        return f'Set[{python_inner}]'
    
    # Handle union types
    if ' | ' in ts_type and not (ts_type.startswith('Union[') or ts_type.startswith('{')):
        # For complex types with nested structures, we need smarter parsing
        parts = []
        current_part = ""
        brace_count = 0
        i = 0
        
        while i < len(ts_type):
            char = ts_type[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            
            # Only split on | when not inside braces
            if char == '|' and brace_count == 0:
                # Check if this is actually a union separator (has spaces around it)
                if i > 0 and i < len(ts_type) - 1 and ts_type[i-1] == ' ' and ts_type[i+1] == ' ':
                    parts.append(current_part.strip())
                    current_part = ""
                    i += 2  # Skip the '| ' part
                    continue
            
            current_part += char
            i += 1
        
        if current_part:
            parts.append(current_part.strip())
        
        if 'null' in parts or 'undefined' in parts:
            # Optional type
            non_null_parts = [p for p in parts if p not in ('null', 'undefined')]
            if len(non_null_parts) == 1:
                required_imports['typing'].add('Optional')
                inner_type = transform_ts_type_to_python(non_null_parts[0], required_imports)
                return f'Optional[{inner_type}]'
        
        # General union
        required_imports['typing'].add('Union')
        python_parts = [transform_ts_type_to_python(p, required_imports) for p in parts]
        return f'Union[{", ".join(python_parts)}]'
    
    # Handle literal types
    if ts_type.startswith('"') and ts_type.endswith('"'):
        required_imports['typing'].add('Literal')
        return f'Literal[{ts_type}]'
    
    # Handle z.infer<...> types
    if ts_type.startswith('z.infer<') and ts_type.endswith('>'):
        # This is a Zod type inference, convert to Any for Python
        required_imports['typing'].add('Any')
        return 'Any'
    
    # Handle object literal types { ... }
    if ts_type.startswith('{') and ts_type.endswith('}'):
        # Complex object types become Dict[str, Any] in Python
        required_imports['typing'].add('Dict')
        required_imports['typing'].add('Any')
        return 'Dict[str, Any]'
    
    # Handle Union[{ ... }] where the union contains a single object literal
    if ts_type.startswith('Union[{') and ts_type.endswith('}]'):
        # This is a union with a single object literal, just convert to Dict
        required_imports['typing'].add('Dict')
        required_imports['typing'].add('Any')
        return 'Dict[str, Any]'
    
    # Check if it's a known DiPeO type
    dipeo_types = {'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'DiagramID', 'ExecutionID', 
                   'NodeType', 'ExecutionStatus', 'LLMService', 'NodeExecutionStatus', 'ApiKeyID'}
    if ts_type in dipeo_types:
        required_imports['dipeo.models'].add(ts_type)
    
    # Default: assume it's a custom type
    return ts_type