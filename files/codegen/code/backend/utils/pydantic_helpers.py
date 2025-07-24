"""Pydantic-specific helper functions."""
from typing import Dict, Any, List, Optional


def build_validators(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build Pydantic validators from spec data."""
    validators = []
    
    for field in spec_data.get('fields', []):
        field_name = field.get('name', '')
        
        # Custom validation logic
        if field.get('validation'):
            for rule in field['validation']:
                validator = {
                    'name': f"validate_{field_name}_{rule['type']}",
                    'field': field_name,
                    'type': rule['type'],
                    'params': rule.get('params', {}),
                    'message': rule.get('message', f"Validation failed for {field_name}")
                }
                validators.append(validator)
        
        # Cross-field validation
        if field.get('depends_on'):
            validator = {
                'name': f"validate_{field_name}_dependencies",
                'field': field_name,
                'type': 'dependency',
                'depends_on': field['depends_on'],
                'root_validator': True
            }
            validators.append(validator)
    
    # Model-level validators
    if spec_data.get('validators'):
        for validator_spec in spec_data['validators']:
            validators.append({
                'name': validator_spec['name'],
                'type': 'model',
                'root_validator': True,
                **validator_spec
            })
    
    return validators


def generate_validator_code(validator: Dict[str, Any]) -> str:
    """Generate Pydantic validator method code."""
    lines = []
    
    if validator.get('root_validator'):
        lines.append("@validator('*', pre=True)")
        lines.append(f"def {validator['name']}(cls, values):")
    else:
        field = validator['field']
        lines.append(f"@validator('{field}')")
        lines.append(f"def {validator['name']}(cls, v, values):")
    
    # Add validation logic based on type
    val_type = validator['type']
    
    if val_type == 'dependency':
        depends_on = validator.get('depends_on', [])
        lines.append(f"    # Check dependencies: {depends_on}")
        lines.append("    for dep in " + str(depends_on) + ":")
        lines.append("        if dep not in values:")
        lines.append(f"            raise ValueError('{validator['field']} requires {depends_on}')")
    
    elif val_type == 'custom':
        lines.append(f"    # Custom validation")
        lines.append(f"    # TODO: Implement custom validation logic")
        lines.append("    pass")
    
    else:
        lines.append(f"    # {val_type} validation")
        lines.append("    # TODO: Implement validation")
        lines.append("    pass")
    
    lines.append("    return v")
    
    return '\n'.join(lines)


def build_model_config(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build Pydantic model Config class attributes."""
    config = {
        'use_enum_values': True,
        'validate_assignment': True,
        'extra': 'forbid',  # Don't allow extra fields by default
    }
    
    # Override with spec config
    if 'model_config' in spec_data:
        config.update(spec_data['model_config'])
    
    # Add schema extra for OpenAPI
    if 'example' in spec_data:
        config['schema_extra'] = {'example': spec_data['example']}
    
    return config


def generate_enum_classes(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate Enum class definitions from field specifications."""
    enums = []
    
    for field in spec_data.get('fields', []):
        if field.get('enum'):
            enum_name = f"{field['name'].title().replace('_', '')}Enum"
            enum_values = field['enum']
            
            enums.append({
                'name': enum_name,
                'field': field['name'],
                'values': enum_values,
                'description': field.get('description', '')
            })
    
    return enums


def get_field_serialization(field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get field serialization configuration."""
    serialization = {}
    
    # Custom serialization
    if field.get('serialize_as'):
        serialization['alias'] = field['serialize_as']
    
    # Exclude from serialization
    if field.get('exclude'):
        serialization['exclude'] = True
    
    # Custom serializer
    if field.get('serializer'):
        serialization['serializer'] = field['serializer']
    
    return serialization if serialization else None


def build_orm_config(spec_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build ORM mode configuration if needed."""
    if not spec_data.get('orm_mode'):
        return None
    
    return {
        'orm_mode': True,
        'table_name': spec_data.get('table_name', spec_data['type'].lower()),
        'relationships': spec_data.get('relationships', [])
    }