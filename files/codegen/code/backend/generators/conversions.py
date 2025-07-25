"""Pure generator for model conversions between TypeScript and Python."""
from typing import Dict, Any, List, Set
from files.codegen.code.shared.template_env import create_template_env
import json


def generate_conversions(all_specs: List[Dict[str, Any]], template_content: str) -> str:
    """
    Pure function: Generate conversion functions between TypeScript and Python models.
    
    Args:
        all_specs: List of all node specifications
        template_content: Jinja2 template content
        
    Returns:
        Generated Python conversion code
    """
    env = create_template_env()
    
    # Extract enums and models from specifications
    enums = _extract_enums_from_specs(all_specs)
    models = _extract_models_from_specs(all_specs)
    
    # Build conversion data matching template expectations
    conversion_data = {
        'enums': enums,
        'models': models
    }
    
    # Wrap in conversion_data for template
    context = {
        'conversion_data': conversion_data
    }
    
    template = env.from_string(template_content)
    return template.render(context)


def _extract_enums_from_specs(specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract enum definitions from node specifications."""
    enums = []
    enum_names = set()
    
    # Common enums used across nodes
    common_enums = [
        {'name': 'NodeType'},
        {'name': 'DiagramFormat'},
        {'name': 'HookType'},
        {'name': 'HookTriggerMode'},
        {'name': 'HttpMethod'},
        {'name': 'LLMService'},
        {'name': 'APIServiceType'},
        {'name': 'NotionOperation'},
        {'name': 'DBBlockSubType'},
        {'name': 'SupportedLanguage'},
    ]
    
    for enum in common_enums:
        if enum['name'] not in enum_names:
            enums.append(enum)
            enum_names.add(enum['name'])
    
    # Extract enums from field definitions
    for spec in specs:
        fields = spec.get('fields', [])
        for field in fields:
            # Check if field type is an enum
            if field.get('type') == 'enum' and 'enumName' in field:
                enum_name = field['enumName']
                if enum_name not in enum_names:
                    enums.append({'name': enum_name})
                    enum_names.add(enum_name)
    
    return enums


def _extract_models_from_specs(specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract model definitions from node specifications."""
    models = []
    
    for spec in specs:
        node_type = spec.get('nodeType', '')
        if not node_type:
            continue
            
        # Convert node_type to class name (e.g., person_job -> PersonJobNodeData)
        class_name = ''.join(word.title() for word in node_type.split('_')) + 'NodeData'
        
        # Extract fields with their types
        fields = {}
        for field in spec.get('fields', []):
            field_name = field.get('name', '')
            field_type = field.get('type', 'string')
            
            # Check if it's an enum field
            field_info = {
                'name': field_name,
                'type': field_type,
                'required': field.get('required', False)
            }
            
            # Map specific fields to their enum types
            if field_name in ['operation', 'sub_type', 'method', 'language', 'code_type', 
                             'hook_type', 'trigger_mode', 'service', 'api_service_type',
                             'format', 'diagram_format']:
                field_info['type'] = _get_enum_type_for_field(field_name, node_type)
            
            fields[field_name] = field_info
        
        model = {
            'name': class_name,
            'type': 'class',  # Template expects this
            'fields': fields
        }
        
        models.append(model)
    
    # For now, skip common models until we decide how to handle them
    # in the new codegen system
    
    return models


def _get_enum_type_for_field(field_name: str, node_type: str) -> str:
    """Get the enum type for a specific field."""
    # Map field names to their enum types
    enum_mappings = {
        'operation': {
            'notion': 'NotionOperation',
            'default': 'str'  # For nodes without specific operation enums
        },
        'sub_type': 'DBBlockSubType',
        'method': 'HttpMethod',
        'language': 'SupportedLanguage',
        'code_type': 'SupportedLanguage',
        'hook_type': 'HookType',
        'trigger_mode': 'HookTriggerMode',
        'service': 'LLMService',
        'api_service_type': 'APIServiceType',
        'format': 'DiagramFormat',
        'diagram_format': 'DiagramFormat'
    }
    
    if field_name in enum_mappings:
        mapping = enum_mappings[field_name]
        if isinstance(mapping, dict):
            return mapping.get(node_type, mapping.get('default', 'str'))
        return mapping
    
    return 'str'  # Default to string


def _load_all_specs(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load all node specifications from batch results."""
    # Handle batch results from sub_diagram
    all_specs = inputs.get('all_specs', {})
    
    if isinstance(all_specs, dict) and 'results' in all_specs:
        # Extract specs from batch results
        specs = []
        for result in all_specs.get('results', []):
            if isinstance(result, dict) and result.get('status') == 'success':
                spec_data = result.get('result', {})
                if isinstance(spec_data, str):
                    spec_data = json.loads(spec_data)
                specs.append(spec_data)
        return specs
    
    # Fallback: try individual spec inputs (for non-batch mode)
    manifest_data = inputs.get('manifest_data', {})
    if isinstance(manifest_data, str):
        manifest_data = json.loads(manifest_data)
    
    node_types = manifest_data.get('nodes', [])
    specs = []
    
    # Load individual specs
    for node_type in node_types:
        spec_data = inputs.get(f'{node_type}_spec')
        if spec_data:
            if isinstance(spec_data, str):
                spec_data = json.loads(spec_data)
            specs.append(spec_data)
    
    return specs


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - manifest_data: Manifest with node list
            - <node_type>_spec: Individual node specifications
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated conversions code
            - filename: Output filename
    """
    template_content = inputs.get('template_content', '')
    
    if not template_content:
        raise ValueError("template_content is required")
    
    # Load all specifications
    all_specs = _load_all_specs(inputs)
    
    generated_code = generate_conversions(all_specs, template_content)
    
    return {
        'generated_code': generated_code,
        'filename': 'conversions.py'
    }