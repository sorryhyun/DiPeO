"""Extract GraphQL types from TypeScript AST data."""

import re


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
    
    # Handle empty object notation {} as array
    if clean_type == '{}':
        return '[String!]'  # Default to string array
    
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
        enums.append({
            'name': enum.get('name'),
            'values': [m.get('name') for m in enum.get('members', [])]
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
        if name.endswith('NodeData'):
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
            if field_type == '{}' or field_type == 'string[]' and graphql_type == '{}':
                # Handle empty object notation as array
                graphql_type = '[String!]'
            elif field_type.startswith('Record<string,'):
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
    
    # Add missing enums with placeholder values
    for enum_name in missing_enums:
        if enum_name in ['LLMService', 'APIServiceType', 'NotionOperation'] and not any(e['name'] == enum_name for e in enums):
            # Add placeholder enums for known missing types
            if enum_name == 'LLMService':
                enums.append({
                    'name': 'LLMService',
                    'values': ['OPENAI', 'ANTHROPIC', 'GOOGLE', 'AZURE']
                })
            elif enum_name == 'APIServiceType':
                enums.append({
                    'name': 'APIServiceType',
                    'values': ['OPENAI', 'ANTHROPIC', 'GOOGLE', 'AZURE', 'CUSTOM']
                })
            elif enum_name == 'NotionOperation':
                enums.append({
                    'name': 'NotionOperation',
                    'values': ['CREATE_PAGE', 'UPDATE_PAGE', 'GET_PAGE', 'DELETE_PAGE', 'QUERY_DATABASE']
                })
    
    return {
        'types': types,
        'input_types': input_types,
        'node_types': node_types
    }


def extract_graphql_types(diagram_ast: dict, execution_ast: dict, conversation_ast: dict) -> dict:
    """Extract all GraphQL types from combined AST data"""
    # Combine all AST data
    all_interfaces = []
    all_enums = []
    all_types = []
    
    for ast in [diagram_ast, execution_ast, conversation_ast]:
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
    print(f"  - {len(type_results['node_types'])} node data types")
    
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


def main(inputs: dict) -> dict:
    """Main entry point for GraphQL types extraction"""
    diagram_ast = inputs.get('diagram_ast', {})
    execution_ast = inputs.get('execution_ast', {})
    conversation_ast = inputs.get('conversation_ast', {})
    
    return extract_graphql_types(diagram_ast, execution_ast, conversation_ast)