"""Conversion functions generator between TypeScript and Python models."""

import os
import sys
from pathlib import Path

# Add parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.template_utils import create_jinja_env, register_enum_filter
from utils.file_utils import load_model_data, save_result_info


def generate_conversions(inputs):
    """Generate conversion functions between TypeScript and Python models."""
    print("[generate_conversions] Starting generation")
    
    try:
        # Load conversion data
        conversion_data = load_model_data('conversion_data.json')
        print(f"[generate_conversions] Loaded conversion data")
        
        # Setup Jinja2 environment
        temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'backend'
        env = create_jinja_env(template_dir)
        
        # Register enum filter with specific enum data
        register_enum_filter(env, conversion_data.get('enums', []))
        
        # Load and render template
        template = env.get_template('conversions.j2')
        content = template.render(conversion_data=conversion_data)
        
        # Write output file with diagram_ prefix to avoid conflicts
        output_dir = Path(temp_dir) / 'dipeo' / 'models'
        output_path = output_dir / 'diagram_generated_conversions.py'
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"[generate_conversions] Generated conversion functions: {output_path}")
        
        # Save result info for combine_results
        result = {'path': str(output_path), 'type': 'conversions'}
        save_result_info('conversion', result)
        
        return {'path': str(output_path), 'type': 'conversions', 'success': True}
        
    except FileNotFoundError as e:
        print(f"[generate_conversions] ERROR: {e}")
        return {'error': str(e)}
    except Exception as e:
        print(f"[generate_conversions] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}