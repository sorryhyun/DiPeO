"""Pure generator for static node implementations."""
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env


def generate_static_node(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate static node implementation from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated Python static node code
    """
    env = create_template_env()
    
    # Add execution-specific data
    node_spec = {
        **spec_data,
        'handler_class': f"{spec_data['nodeType'].title().replace('_', '')}NodeHandler",
        'node_class': f"{spec_data['nodeType'].title().replace('_', '')}Node",
        'execution_logic': _build_execution_logic(spec_data),
        'input_handlers': _build_input_handlers(spec_data),
        'output_handlers': _build_output_handlers(spec_data),
        'validation_logic': _build_validation_logic(spec_data),
        'imports': _calculate_imports(spec_data),
    }
    
    # Create context with both original spec and enhanced data
    context = {
        **spec_data,  # All original fields (nodeType, displayName, fields, etc.)
        **node_spec,  # Enhanced node-specific data
    }
    
    template = env.from_string(template_content)
    return template.render(context)


def _build_execution_logic(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the execution logic structure for the node."""
    node_type = spec_data.get('nodeType', '')
    
    execution = {
        'pre_execute': [],
        'main_execute': [],
        'post_execute': [],
        'error_handlers': [],
    }
    
    # Add type-specific logic
    if node_type == 'person_job':
        execution['main_execute'] = [
            "# Execute LLM call",
            "llm_service = self.container.get('llm_service')",
            "response = await llm_service.generate(",
            "    prompt=node.props.get('default_prompt', ''),",
            "    model=node.props.get('model'),",
            "    temperature=node.props.get('temperature', 0.7)",
            ")",
            "return {'content': response.content}"
        ]
    elif node_type == 'code_job':
        execution['main_execute'] = [
            "# Execute code",
            "code_executor = self.container.get('code_executor')",
            "result = await code_executor.execute(",
            "    code=node.props.get('code', ''),",
            "    language=node.props.get('code_type', 'python'),",
            "    inputs=inputs",
            ")",
            "return result"
        ]
    elif node_type == 'api_job':
        execution['main_execute'] = [
            "# Make API request",
            "http_client = self.container.get('http_client')",
            "response = await http_client.request(",
            "    method=node.props.get('method', 'GET'),",
            "    url=node.props.get('url'),",
            "    headers=node.props.get('headers', {}),",
            "    data=node.props.get('body')",
            ")",
            "return {'response': response.json()}"
        ]
    elif node_type == 'condition':
        execution['main_execute'] = [
            "# Evaluate condition",
            "condition_type = node.props.get('condition_type')",
            "if condition_type == 'custom':",
            "    expression = node.props.get('expression', 'True')",
            "    result = eval(expression, {'__builtins__': {}}, inputs)",
            "elif condition_type == 'detect_max_iterations':",
            "    # Check if all person_job nodes reached max",
            "    result = self._check_max_iterations(context)",
            "else:",
            "    result = True",
            "return {'result': bool(result)}"
        ]
    else:
        execution['main_execute'] = [
            "# Default execution logic",
            "# TODO: Implement node-specific logic",
            "return {'result': 'success'}"
        ]
    
    # Add common error handlers
    execution['error_handlers'] = [
        {
            'exception': 'ValidationError',
            'handler': 'self._handle_validation_error'
        },
        {
            'exception': 'TimeoutError',
            'handler': 'self._handle_timeout_error'
        },
        {
            'exception': 'Exception',
            'handler': 'self._handle_generic_error'
        }
    ]
    
    return execution


def _build_input_handlers(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build input processing handlers."""
    handlers = []
    
    # Add handler for each expected input type
    for field in spec_data.get('fields', []):
        if field.get('from_input'):
            handlers.append({
                'name': field['name'],
                'type': field.get('type', 'string'),
                'required': field.get('required', False),
                'processor': f"self._process_{field['name']}_input"
            })
    
    # Add default handlers
    handlers.extend([
        {
            'name': '_default',
            'type': 'any',
            'required': False,
            'processor': 'self._process_default_input'
        }
    ])
    
    return handlers


def _build_output_handlers(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build output processing handlers."""
    handlers = []
    
    # Output formatting based on node type
    node_type = spec_data.get('nodeType', '')
    
    if node_type in ['person_job', 'code_job']:
        handlers.append({
            'name': 'content',
            'formatter': 'self._format_content_output'
        })
    
    if node_type == 'condition':
        handlers.extend([
            {
                'name': 'true_output',
                'condition': 'result == True',
                'formatter': 'self._format_true_output'
            },
            {
                'name': 'false_output',
                'condition': 'result == False',
                'formatter': 'self._format_false_output'
            }
        ])
    
    # Default output handler
    handlers.append({
        'name': 'default',
        'formatter': 'self._format_default_output'
    })
    
    return handlers


def _build_validation_logic(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build validation logic for the node."""
    validation = {
        'pre_validation': [],
        'post_validation': [],
        'custom_validators': []
    }
    
    # Add field validations
    for field in spec_data.get('fields', []):
        if field.get('required'):
            validation['pre_validation'].append(
                f"if '{field['name']}' not in node.props:"
                f"    raise ValidationError('Missing required field: {field['name']}')"
            )
    
    # Add type-specific validations
    node_type = spec_data.get('nodeType', '')
    if node_type == 'api_job':
        validation['pre_validation'].extend([
            "if not node.props.get('url'):",
            "    raise ValidationError('API job requires URL')"
        ])
    elif node_type == 'code_job':
        validation['pre_validation'].extend([
            "if not node.props.get('code'):",
            "    raise ValidationError('Code job requires code')"
        ])
    
    return validation


def _calculate_imports(spec_data: Dict[str, Any]) -> List[str]:
    """Calculate Python imports needed for the static node."""
    imports = [
        "from typing import Dict, Any, List, Optional",
        "from dipeo.core.models import BaseNode",
        "from dipeo.core.handlers import BaseNodeHandler",
        "from dipeo.core.exceptions import ValidationError, ExecutionError",
    ]
    
    # Add type-specific imports
    node_type = spec_data.get('nodeType', '')
    if node_type == 'person_job':
        imports.append("from dipeo.core.services import LLMService")
    elif node_type == 'code_job':
        imports.append("from dipeo.core.services import CodeExecutor")
    elif node_type == 'api_job':
        imports.append("from dipeo.core.services import HTTPClient")
    
    return sorted(list(set(imports)))


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - spec_data: Node specification
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated static node code
            - filename: Suggested filename for the output
            - metadata: Handler metadata
    """
    try:
        spec_data = inputs.get('spec_data', {})
        template_content = inputs.get('template_content', '')
        
        if not spec_data:
            raise ValueError("spec_data is required")
        if not template_content:
            raise ValueError("template_content is required")
        
        generated_code = generate_static_node(spec_data, template_content)
        
        # Generate filename from node type
        node_type = spec_data.get('nodeType', 'unknown')
        filename = f"{node_type}_node.py"
        
        # Generate metadata
        metadata = {
            'node_type': node_type,
            'handler': f"{node_type}_handler",
            'validator': f"validate_{node_type}",
            'executor': f"execute_{node_type}",
        }
        
        return {
            'generated_code': generated_code,
            'filename': filename,
            'metadata': metadata
        }
    except Exception as e:
        # Return the error in the expected format for debugging
        import traceback
        return {
            'generated_code': f"# ERROR in static_nodes.py:\n# {str(e)}\n# Traceback:\n# {traceback.format_exc()}",
            'filename': 'error.py',
            'metadata': {'error': str(e)}
        }