"""TypeScript to Python type transformation utilities."""

from typing import Any


def transform_ts_to_python(ast_data: dict[str, Any]) -> dict[str, Any]:
    """Transform TypeScript AST to Python type definitions.
    
    This utility converts TypeScript types extracted from AST
    into their Python equivalents, useful for code generation
    and cross-language type mapping.
    
    Args:
        ast_data: Dictionary containing parsed TypeScript AST data with keys:
            - interfaces: List of interface definitions
            - types: List of type alias definitions
            - enums: List of enum definitions
    
    Returns:
        Dictionary containing:
            - classes: Python dataclass representations of interfaces
            - types: Python type alias definitions
            - enums: Python enum definitions
            - imports: Required Python import statements
    
    Example:
        >>> ast_data = {
        ...     'interfaces': [{'name': 'User', 'properties': [...]}],
        ...     'types': [{'name': 'UserRole', 'type': 'string'}],
        ...     'enums': [{'name': 'Status', 'members': [...]}]
        ... }
        >>> result = transform_ts_to_python(ast_data)
        >>> print(result['classes'][0]['name'])  # 'User'
    """
    interfaces = ast_data.get('interfaces', [])
    types = ast_data.get('types', [])
    enums = ast_data.get('enums', [])
    
    # Transform interfaces to Python dataclasses
    python_classes = []
    for interface in interfaces:
        fields = []
        for prop in interface.get('properties', []):
            py_type = map_ts_type_to_python(prop['type'])
            if prop.get('optional', False):
                py_type = f'Optional[{py_type}]'
            
            fields.append({
                'name': prop['name'],
                'type': py_type,
                'optional': prop.get('optional', False),
                'readonly': prop.get('readonly', False),
                'jsDoc': prop.get('jsDoc')
            })
        
        python_classes.append({
            'name': interface['name'],
            'fields': fields,
            'extends': interface.get('extends', []),
            'isExported': interface.get('isExported', True),
            'jsDoc': interface.get('jsDoc')
        })
    
    # Transform type aliases
    python_types = []
    for type_alias in types:
        python_types.append({
            'name': type_alias['name'],
            'type': map_ts_type_to_python(type_alias['type']),
            'isExported': type_alias.get('isExported', True),
            'jsDoc': type_alias.get('jsDoc')
        })
    
    # Transform enums
    python_enums = []
    for enum in enums:
        python_enums.append({
            'name': enum['name'],
            'members': enum.get('members', []),
            'isExported': enum.get('isExported', True),
            'jsDoc': enum.get('jsDoc')
        })
    
    return {
        'classes': python_classes,
        'types': python_types,
        'enums': python_enums,
        'imports': [
            'from typing import Dict, List, Optional, Union, Any, Literal, Awaitable',
            'from datetime import datetime',
            'from dataclasses import dataclass, field'
        ]
    }


def map_ts_type_to_python(ts_type: str) -> str:
    """Map a TypeScript type to its Python equivalent.
    
    Handles various TypeScript type patterns including:
    - Basic types (string, number, boolean)
    - Array types (T[] or Array<T>)
    - Generic types (Promise<T>, Record<K,V>)
    - Union types (A | B | C)
    - Literal types ("literal")
    
    Args:
        ts_type: TypeScript type string
    
    Returns:
        Python type string
    
    Examples:
        >>> map_ts_type_to_python('string')
        'str'
        >>> map_ts_type_to_python('number[]')
        'List[float]'
        >>> map_ts_type_to_python('Promise<string>')
        'Awaitable[str]'
        >>> map_ts_type_to_python('string | number')
        'Union[str, float]'
    """
    # Type mapping from TypeScript to Python
    basic_type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'Date': 'datetime',
        'any': 'Any',
        'unknown': 'Any',
        'void': 'None',
        'null': 'None',
        'undefined': 'Optional[Any]',
        'object': 'Dict[str, Any]',
        'Object': 'Dict[str, Any]',
        'Array': 'List',
        'Promise': 'Awaitable'
    }
    
    # Handle array types (e.g., string[])
    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        return f'List[{map_ts_type_to_python(inner_type)}]'
    
    # Handle generic types (e.g., Array<string>, Promise<T>)
    if '<' in ts_type and '>' in ts_type:
        base = ts_type[:ts_type.index('<')]
        inner = ts_type[ts_type.index('<')+1:ts_type.rindex('>')]
        
        if base == 'Array':
            return f'List[{map_ts_type_to_python(inner)}]'
        elif base == 'Promise':
            return f'Awaitable[{map_ts_type_to_python(inner)}]'
        elif base == 'Record':
            # Record<K, V> -> Dict[K, V]
            parts = inner.split(',', 1)
            if len(parts) == 2:
                key_type = map_ts_type_to_python(parts[0].strip())
                value_type = map_ts_type_to_python(parts[1].strip())
                return f'Dict[{key_type}, {value_type}]'
        elif base == 'Partial':
            # Partial<T> -> Optional fields
            return f'Partial[{map_ts_type_to_python(inner)}]'
        elif base == 'Required':
            # Required<T> -> Non-optional fields
            return f'Required[{map_ts_type_to_python(inner)}]'
        elif base == 'ReadonlyArray':
            return f'Sequence[{map_ts_type_to_python(inner)}]'
        
        # Generic type not explicitly handled
        return f'{base}[{inner}]'
    
    # Handle union types (e.g., string | number)
    if '|' in ts_type:
        parts = [map_ts_type_to_python(p.strip()) for p in ts_type.split('|')]
        return f'Union[{", ".join(parts)}]'
    
    # Handle intersection types (e.g., A & B)
    # Note: Python doesn't have direct intersection types, we approximate
    if '&' in ts_type:
        parts = [p.strip() for p in ts_type.split('&')]
        # For now, just return the first type with a comment
        # In a real implementation, you might want to handle this differently
        return f'{map_ts_type_to_python(parts[0])}  # Intersection: {ts_type}'
    
    # Handle literal types (e.g., "literal" or 'literal')
    if (ts_type.startswith('"') and ts_type.endswith('"')) or \
       (ts_type.startswith("'") and ts_type.endswith("'")):
        return f'Literal[{ts_type}]'
    
    # Handle tuple types (e.g., [string, number])
    if ts_type.startswith('[') and ts_type.endswith(']'):
        elements = ts_type[1:-1].split(',')
        mapped_elements = [map_ts_type_to_python(e.strip()) for e in elements]
        return f'tuple[{", ".join(mapped_elements)}]'
    
    # Map basic types or return as-is if not in map
    return basic_type_map.get(ts_type, ts_type)


def get_python_imports_for_types(types: list[str]) -> list[str]:
    """Generate Python import statements based on used types.
    
    Analyzes a list of Python type strings and generates the
    necessary import statements.
    
    Args:
        types: List of Python type strings
    
    Returns:
        List of import statements
    
    Example:
        >>> types = ['str', 'List[str]', 'Optional[int]', 'datetime']
        >>> imports = get_python_imports_for_types(types)
        >>> 'from typing import List, Optional' in imports
        True
    """
    typing_imports = set()
    other_imports = set()
    
    for type_str in types:
        # Check for typing module types
        if 'Dict' in type_str:
            typing_imports.add('Dict')
        if 'List' in type_str:
            typing_imports.add('List')
        if 'Optional' in type_str:
            typing_imports.add('Optional')
        if 'Union' in type_str:
            typing_imports.add('Union')
        if 'Any' in type_str:
            typing_imports.add('Any')
        if 'Literal' in type_str:
            typing_imports.add('Literal')
        if 'Awaitable' in type_str:
            typing_imports.add('Awaitable')
        if 'Sequence' in type_str:
            typing_imports.add('Sequence')
        if 'tuple' in type_str.lower():
            typing_imports.add('Tuple')
        
        # Check for other imports
        if 'datetime' in type_str:
            other_imports.add('from datetime import datetime')
        if 'dataclass' in type_str:
            other_imports.add('from dataclasses import dataclass, field')
    
    imports = []
    
    if typing_imports:
        imports.append(f'from typing import {", ".join(sorted(typing_imports))}')
    
    imports.extend(sorted(other_imports))
    
    return imports