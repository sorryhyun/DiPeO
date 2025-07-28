from datetime import datetime
from jinja2 import Template, StrictUndefined


def main(inputs):
    # Get template content - it comes as a direct string input
    template_content = inputs.get('template_content', '')
    
    # Get prepared data - it comes from the 'default' connection
    template_data = inputs.get('default', {})
    
    # Ensure all expected keys exist with proper defaults
    template_context = {
        'scalars': template_data.get('scalars', []),
        'enums': template_data.get('enums', []),
        'types': template_data.get('types', []),
        'input_types': template_data.get('input_types', []),
        'node_types': template_data.get('node_types', []),
        'now': template_data.get('now', datetime.now().isoformat())
    }
    
    # Render template with error handling
    try:
        jinja_template = Template(template_content, undefined=StrictUndefined)
        rendered = jinja_template.render(**template_context)
        # Return the rendered content as 'generated_code' for DB node
        result = {'generated_code': rendered}
    except Exception as e:
        import traceback
        error_msg = f"Template rendering error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # Return the error as the generated content so we can see it
        result = {'generated_code': error_msg}
    
    return result