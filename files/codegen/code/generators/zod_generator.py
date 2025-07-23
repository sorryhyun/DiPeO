"""Zod schemas generator for TypeScript runtime validation."""

import os
from pathlib import Path
from ..utils.template_utils import create_jinja_env, register_enum_filter
from ..utils.file_utils import load_model_data, save_result_info
from ..utils.type_converters import to_zod_type, to_zod_schema


def generate_zod_schemas(inputs):
    """Generate Zod schemas for TypeScript runtime validation."""
    print("[generate_zod_schemas] Starting generation")
    
    try:
        # Load zod data
        zod_data = load_model_data('zod_data.json')
        print(f"[generate_zod_schemas] Loaded zod data")
        
        # Setup Jinja2 environment
        temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'backend'
        env = create_jinja_env(template_dir)
        
        # Register enum filter
        register_enum_filter(env, zod_data.get('enums', []))
        
        # Create is_enum function for to_zod_type
        enums = {enum['name'] for enum in zod_data.get('enums', [])}
        is_enum_func = lambda type_name: type_name in enums
        
        # Register additional filters for Zod
        env.filters['toZodSchema'] = to_zod_schema
        env.filters['toZodType'] = lambda field: to_zod_type(field, is_enum_func)
        
        # Load and render template
        template = env.get_template('zod_schemas.j2')
        content = template.render(zod_data=zod_data)
        
        # Write output file
        output_dir = Path(temp_dir) / 'dipeo' / 'models' / 'src' / 'generated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'zod_schemas.ts'
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"[generate_zod_schemas] Generated Zod schemas: {output_path}")
        
        # Save result info for combine_results
        result = {'path': str(output_path), 'type': 'zod_schemas'}
        save_result_info('zod', result)
        
        return {'path': str(output_path), 'type': 'zod_schemas', 'success': True}
        
    except FileNotFoundError as e:
        print(f"[generate_zod_schemas] ERROR: {e}")
        return {'error': str(e)}
    except Exception as e:
        print(f"[generate_zod_schemas] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}