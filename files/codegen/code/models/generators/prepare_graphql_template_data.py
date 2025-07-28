from datetime import datetime


def main(inputs):
    graphql_types = inputs.get('graphql_types', {})
    
    # Prepare the template data
    template_data = {
        'scalars': graphql_types.get('scalars', []),
        'enums': graphql_types.get('enums', []),
        'types': graphql_types.get('types', []),
        'input_types': graphql_types.get('input_types', []),
        'node_types': graphql_types.get('node_types', []),
        'now': datetime.now().isoformat()
    }
    
    return template_data