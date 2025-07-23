"""GraphQL schema generator from Python models."""

import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..utils.file_utils import load_model_data, save_result_info
from ..utils.type_converters import python_to_graphql_type


def generate_graphql_schema(inputs):
    """Generate GraphQL schema from Python models."""
    print("[generate_graphql_schema] Starting generation")
    
    try:
        # Load model data
        model_data = load_model_data()
        print(f"[generate_graphql_schema] Loaded model data")
        
        # Prepare GraphQL data structure
        graphql_data = {
            'enums': [],
            'models': [],
            'unions': {}
        }
        
        # Extract enum names for type conversion
        enum_names = {enum['name'] for enum in model_data.get('models', []) 
                      if enum.get('type') == 'enum'}
        
        # Process enums
        for model in model_data.get('models', []):
            if model.get('type') == 'enum':
                graphql_data['enums'].append({
                    'name': model['name'],
                    'values': [v[0] for v in model.get('enum_values', [])]
                })
        
        # Process models
        for model in model_data.get('models', []):
            if model.get('type') == 'class':
                fields = []
                for field_name, field_info in model.get('fields', {}).items():
                    fields.append({
                        'name': field_name,
                        'graphql_type': python_to_graphql_type(
                            field_info['type'], enum_names
                        ),
                        'required': field_info.get('required', True),
                        'description': field_info.get('description', '')
                    })
                
                graphql_data['models'].append({
                    'name': model['name'],
                    'fields': fields
                })
        
        # Setup Jinja2 environment
        temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'backend'
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape()
        )
        
        # Load and render template
        template = env.get_template('graphql_from_python.j2')
        content = template.render(graphql_data=graphql_data)
        
        # Write output file
        output_dir = Path(temp_dir) / 'apps' / 'server' / 'src' / 'dipeo_server' / 'api' / 'graphql' / 'schema'
        output_dir.mkdir(exist_ok=True, parents=True)
        output_path = output_dir / 'generated_models.graphql'
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"[generate_graphql_schema] Generated GraphQL schema: {output_path}")
        
        # Save result info for combine_results
        result = {'path': str(output_path), 'type': 'graphql_schema'}
        save_result_info('graphql', result)
        
        return {'path': str(output_path), 'type': 'graphql_schema', 'success': True}
        
    except FileNotFoundError as e:
        print(f"[generate_graphql_schema] ERROR: {e}")
        return {'error': str(e)}
    except Exception as e:
        print(f"[generate_graphql_schema] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}