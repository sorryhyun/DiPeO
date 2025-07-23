"""Pydantic models generator from TypeScript data."""

import os
from pathlib import Path
from ..utils.template_utils import create_jinja_env, register_enum_filter
from ..utils.file_utils import load_model_data, save_result_info


def generate_pydantic_models(inputs):
    """Generate Pydantic models from parsed TypeScript data."""
    print("[generate_pydantic_models] Starting generation")
    
    try:
        # Load model data
        model_data = load_model_data()
        print(f"[generate_pydantic_models] Loaded model data with {len(model_data.get('models', []))} models")
        
        if not model_data or not model_data.get('models'):
            print("[generate_pydantic_models] No models to generate")
            return {'error': 'No models found in model data'}
        
        # Setup Jinja2 environment
        temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'backend'
        env = create_jinja_env(template_dir)
        
        # Register enum filter with specific enum data
        register_enum_filter(env, model_data.get('enums', []))
        
        # Load and render template
        template = env.get_template('pydantic_models.j2')
        content = template.render(model_data=model_data)
        
        # Write output file
        output_dir = Path(temp_dir) / 'dipeo' / 'models'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / 'models.py'
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"[generate_pydantic_models] Generated Pydantic models: {output_path}")
        
        # Save result info for combine_results
        result = {'path': str(output_path), 'type': 'pydantic_models'}
        save_result_info('pydantic', result)
        
        return {'path': str(output_path), 'type': 'pydantic_models', 'success': True}
        
    except FileNotFoundError as e:
        print(f"[generate_pydantic_models] ERROR: {e}")
        return {'error': str(e)}
    except Exception as e:
        print(f"[generate_pydantic_models] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}