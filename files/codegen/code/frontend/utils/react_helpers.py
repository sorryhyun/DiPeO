"""React and UI-related helper functions."""
from typing import Dict, Any, List


def get_field_component(field: Dict[str, Any]) -> str:
    """Determine the appropriate React component for a field."""
    field_type = field.get('type', 'string')
    ui_type = field.get('ui_type')
    
    # Check for explicit UI type
    if ui_type:
        component_map = {
            'textarea': 'TextArea',
            'select': 'Select',
            'radio': 'RadioGroup',
            'checkbox': 'Checkbox',
            'switch': 'Switch',
            'slider': 'Slider',
            'datepicker': 'DatePicker',
            'colorpicker': 'ColorPicker',
            'code': 'CodeEditor',
            'json': 'JsonEditor',
        }
        return component_map.get(ui_type, 'Input')
    
    # Infer from type and properties
    if field.get('enum'):
        return 'Select'
    elif field_type == 'boolean':
        return 'Switch'
    elif field_type in ['text', 'string'] and field.get('multiline'):
        return 'TextArea'
    elif field_type in ['int', 'integer', 'float', 'number']:
        return 'NumberInput'
    elif field_type in ['date', 'datetime']:
        return 'DatePicker'
    elif field_type == 'array':
        return 'ArrayInput'
    elif field_type == 'object':
        return 'JsonEditor'
    else:
        return 'Input'


def get_field_props(field: Dict[str, Any]) -> Dict[str, Any]:
    """Generate React component props for a field."""
    props = {
        'label': field.get('displayName', field.get('name')),
        'name': field.get('name'),
        'required': field.get('required', False),
    }
    
    # Add description as help text
    if 'description' in field:
        props['help'] = field['description']
    
    # Add placeholder
    if 'placeholder' in field:
        props['placeholder'] = field['placeholder']
    
    # Add validation props
    if 'min' in field:
        props['min'] = field['min']
    if 'max' in field:
        props['max'] = field['max']
    if 'pattern' in field:
        props['pattern'] = field['pattern']
    
    # Add enum options
    if 'enum' in field:
        props['options'] = [
            {'label': str(val), 'value': val}
            for val in field['enum']
        ]
    
    # Component-specific props
    component = get_field_component(field)
    if component == 'TextArea':
        props['rows'] = field.get('rows', 4)
    elif component == 'CodeEditor':
        props['language'] = field.get('language', 'javascript')
        props['theme'] = field.get('theme', 'monokai')
    
    return props


def group_fields_for_ui(fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group fields by category for organized UI rendering."""
    groups = {}
    
    for field in fields:
        category = field.get('category', 'General')
        if category not in groups:
            groups[category] = []
        groups[category].append(field)
    
    # Sort groups by priority
    priority_order = ['General', 'Required', 'Advanced', 'Other']
    sorted_groups = {}
    
    for category in priority_order:
        if category in groups:
            sorted_groups[category] = groups[category]
    
    # Add any remaining categories
    for category, fields in groups.items():
        if category not in sorted_groups:
            sorted_groups[category] = fields
    
    return sorted_groups


def get_icon_for_node_type(node_type: str) -> str:
    """Get appropriate icon name for a node type."""
    icon_map = {
        'person_job': 'UserIcon',
        'code_job': 'CodeIcon',
        'api_job': 'CloudIcon',
        'condition': 'GitBranchIcon',
        'db': 'DatabaseIcon',
        'endpoint': 'SaveIcon',
        'start': 'PlayIcon',
        'user_response': 'MessageSquareIcon',
        'sub_diagram': 'LayersIcon',
    }
    return icon_map.get(node_type, 'BoxIcon')


def get_node_color(node_type: str) -> str:
    """Get color scheme for a node type."""
    color_map = {
        'person_job': '#8B5CF6',  # Purple
        'code_job': '#10B981',    # Green
        'api_job': '#3B82F6',     # Blue
        'condition': '#F59E0B',   # Yellow
        'db': '#6366F1',          # Indigo
        'endpoint': '#EF4444',    # Red
        'start': '#10B981',       # Green
        'user_response': '#06B6D4', # Cyan
        'sub_diagram': '#8B5CF6', # Purple
    }
    return color_map.get(node_type, '#6B7280')  # Gray default


def calculate_default_form_values(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate default form values for all fields."""
    defaults = {}
    
    for field in fields:
        name = field.get('name')
        if not name:
            continue
            
        # Use explicit default if provided
        if 'default' in field:
            defaults[name] = field['default']
        else:
            # Generate based on type
            field_type = field.get('type', 'string')
            if field_type in ['string', 'text']:
                defaults[name] = ''
            elif field_type in ['int', 'integer']:
                defaults[name] = 0
            elif field_type in ['float', 'number']:
                defaults[name] = 0.0
            elif field_type == 'boolean':
                defaults[name] = False
            elif field_type == 'array':
                defaults[name] = []
            elif field_type == 'object':
                defaults[name] = {}
            else:
                defaults[name] = None
    
    return defaults