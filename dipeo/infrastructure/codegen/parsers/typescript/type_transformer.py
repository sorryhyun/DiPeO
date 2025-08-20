"""TypeScript to Python type transformation utilities."""


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