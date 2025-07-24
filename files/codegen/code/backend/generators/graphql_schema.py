"""Pure generator for GraphQL schemas."""
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env


def map_to_graphql_type(field_type: str, required: bool = False) -> str:
    """Map generic field types to GraphQL types."""
    type_map = {
        'string': 'String',
        'str': 'String',
        'text': 'String',
        'int': 'Int',
        'integer': 'Int',
        'float': 'Float',
        'number': 'Float',
        'double': 'Float',
        'bool': 'Boolean',
        'boolean': 'Boolean',
        'dict': 'JSON',
        'object': 'JSON',
        'any': 'JSON',
        'date': 'Date',
        'datetime': 'DateTime',
        'time': 'Time',
        'uuid': 'ID',
        'id': 'ID',
    }
    
    # Handle array types
    if field_type.endswith('[]'):
        base_type = field_type[:-2]
        inner_type = map_to_graphql_type(base_type, True)
        return f"[{inner_type}]{'!' if required else ''}"
    
    # Handle List/Array notation
    if field_type.lower().startswith(('list[', 'array[')):
        inner_type = field_type.split('[')[1].rstrip(']')
        mapped_inner = map_to_graphql_type(inner_type, True)
        return f"[{mapped_inner}]{'!' if required else ''}"
    
    base_type = type_map.get(field_type.lower(), 'JSON')
    return f"{base_type}{'!' if required else ''}"


def generate_graphql_schema(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate GraphQL schema from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated GraphQL schema
    """
    env = create_template_env()
    
    # Transform spec for GraphQL
    gql_spec = {
        **spec_data,
        'type_name': f"{spec_data['nodeType'].title().replace('_', '')}Node",
        'input_type_name': f"{spec_data['nodeType'].title().replace('_', '')}NodeInput",
        'fields': [],
        'enums': [],
        'interfaces': spec_data.get('interfaces', ['Node']),
    }
    
    # Process fields
    for field in spec_data.get('fields', []):
        gql_field = {
            'name': field['name'],
            'type': map_to_graphql_type(
                field.get('type', 'string'),
                field.get('required', False)
            ),
            'description': field.get('description', ''),
            'deprecated': field.get('deprecated', False),
            'deprecation_reason': field.get('deprecation_reason', ''),
        }
        
        # Handle enum fields
        if field.get('enum'):
            enum_name = f"{field['name'].title().replace('_', '')}Enum"
            gql_field['type'] = f"{enum_name}{'!' if field.get('required') else ''}"
            
            gql_spec['enums'].append({
                'name': enum_name,
                'values': [
                    {'name': str(val).upper().replace(' ', '_'), 'value': val}
                    for val in field['enum']
                ],
                'description': f"Enum for {field['name']} field"
            })
        
        gql_spec['fields'].append(gql_field)
    
    # Add standard Node interface fields
    gql_spec['node_fields'] = [
        {'name': 'id', 'type': 'ID!', 'description': 'Unique identifier'},
        {'name': 'type', 'type': 'String!', 'description': 'Node type'},
        {'name': 'label', 'type': 'String', 'description': 'Node label'},
        {'name': 'position', 'type': 'Position!', 'description': 'Node position'},
    ]
    
    # Generate queries and mutations
    gql_spec['queries'] = _generate_queries(gql_spec)
    gql_spec['mutations'] = _generate_mutations(gql_spec)
    gql_spec['subscriptions'] = _generate_subscriptions(gql_spec)
    
    template = env.from_string(template_content)
    return template.render(gql_spec)


def _generate_queries(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate GraphQL queries for the node type."""
    type_name = spec['type_name']
    type_lower = spec['nodeType'].replace('_', '')
    
    return [
        {
            'name': f"get{type_name}",
            'args': [{'name': 'id', 'type': 'ID!'}],
            'return_type': type_name,
            'description': f"Get a single {type_name} by ID"
        },
        {
            'name': f"list{type_name}s",
            'args': [
                {'name': 'first', 'type': 'Int', 'default': 10},
                {'name': 'after', 'type': 'String'},
                {'name': 'filter', 'type': f"{type_name}Filter"}
            ],
            'return_type': f"{type_name}Connection!",
            'description': f"List all {type_name}s with pagination"
        },
        {
            'name': f"search{type_name}s",
            'args': [
                {'name': 'query', 'type': 'String!'},
                {'name': 'limit', 'type': 'Int', 'default': 10}
            ],
            'return_type': f"[{type_name}!]!",
            'description': f"Search {type_name}s by text"
        }
    ]


def _generate_mutations(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate GraphQL mutations for the node type."""
    type_name = spec['type_name']
    input_type = spec['input_type_name']
    
    return [
        {
            'name': f"create{type_name}",
            'args': [{'name': 'input', 'type': f"{input_type}!"}],
            'return_type': type_name,
            'description': f"Create a new {type_name}"
        },
        {
            'name': f"update{type_name}",
            'args': [
                {'name': 'id', 'type': 'ID!'},
                {'name': 'input', 'type': input_type}
            ],
            'return_type': type_name,
            'description': f"Update an existing {type_name}"
        },
        {
            'name': f"delete{type_name}",
            'args': [{'name': 'id', 'type': 'ID!'}],
            'return_type': 'Boolean!',
            'description': f"Delete a {type_name}"
        }
    ]


def _generate_subscriptions(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate GraphQL subscriptions for the node type."""
    type_name = spec['type_name']
    
    return [
        {
            'name': f"{spec['nodeType']}Created",
            'return_type': type_name,
            'description': f"Subscribe to new {type_name} creations"
        },
        {
            'name': f"{spec['nodeType']}Updated",
            'args': [{'name': 'id', 'type': 'ID'}],
            'return_type': type_name,
            'description': f"Subscribe to {type_name} updates"
        },
        {
            'name': f"{spec['nodeType']}Deleted",
            'return_type': 'ID!',
            'description': f"Subscribe to {type_name} deletions"
        }
    ]


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - spec_data: Node specification
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated GraphQL schema
            - filename: Suggested filename for the output
    """
    spec_data = inputs.get('spec_data', {})
    template_content = inputs.get('template_content', '')
    
    if not spec_data:
        raise ValueError("spec_data is required")
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_graphql_schema(spec_data, template_content)
    
    # Generate filename from node type
    node_type = spec_data.get('nodeType', 'unknown')
    filename = f"{node_type}.graphql"
    
    return {
        'generated_code': generated_code,
        'filename': filename,
        'node_type': node_type
    }