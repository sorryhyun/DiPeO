"""Conversion functions generator between TypeScript and Python models."""

from pathlib import Path

# Import from parent utils module
from ..utils.template_utils import create_jinja_env, register_enum_filter
from ..utils.file_utils import load_model_data, save_result_info

# Get paths relative to this file
# generators/ -> code/ -> codegen/ -> files/ -> project_root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "files/codegen/templates"


def generate_conversions(inputs):
    """Generate conversion functions between TypeScript and Python models."""
    print("[generate_conversions] Starting generation")
    
    try:
        # Load conversion data
        conversion_data = load_model_data('conversion_data.json')
        print(f"[generate_conversions] Loaded conversion data")
        
        # Setup Jinja2 environment
        template_dir = TEMPLATES_DIR / 'backend'
        env = create_jinja_env(str(template_dir))
        
        # Register enum filter with specific enum data
        register_enum_filter(env, conversion_data.get('enums', []))
        
        # Load and render template
        template = env.get_template('conversions.j2')
        content = template.render(conversion_data=conversion_data)
        
        # Write output file with diagram_ prefix to avoid conflicts
        output_dir = PROJECT_ROOT / 'dipeo' / 'diagram_generated'
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