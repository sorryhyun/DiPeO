"""Utilities for working with node specifications."""
import json
from typing import Dict, Any, List, Optional


def validate_spec(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a node specification."""
    required_fields = ['type', 'displayName', 'fields']
    
    for field in required_fields:
        if field not in spec_data:
            raise ValueError(f"Missing required field in spec: {field}")
    
    # Normalize fields
    normalized_spec = spec_data.copy()
    
    # Ensure each field has required properties
    for field in normalized_spec.get('fields', []):
        if 'name' not in field:
            raise ValueError(f"Field missing 'name' property")
        if 'type' not in field:
            field['type'] = 'string'  # Default type
        if 'required' not in field:
            field['required'] = False
    
    return normalized_spec


def group_fields_by_category(spec_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Group fields by their category for organized UI rendering."""
    fields = spec_data.get('fields', [])
    grouped = {}
    
    for field in fields:
        category = field.get('category', 'General')
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(field)
    
    return grouped


def get_field_by_name(spec_data: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific field from the spec by name."""
    for field in spec_data.get('fields', []):
        if field.get('name') == field_name:
            return field
    return None


def calculate_imports(spec_data: Dict[str, Any], language: str = 'typescript') -> List[str]:
    """Calculate necessary imports based on field types."""
    imports = []
    field_types = set()
    
    for field in spec_data.get('fields', []):
        field_type = field.get('type', 'string')
        field_types.add(field_type)
    
    if language == 'typescript':
        # Add imports based on types used
        if any(t in field_types for t in ['array', 'list']):
            imports.append("import { z } from 'zod';")
        
        # Always import base node
        imports.append("import { BaseNode } from '../base';")
        
    elif language == 'python':
        # Python imports
        imports.append("from typing import Dict, Any, List, Optional")
        imports.append("from pydantic import Field")
        imports.append("from dipeo.core.models import BaseNode")
    
    return imports


def merge_specs(*specs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple specifications, with later specs overriding earlier ones."""
    result = {}
    
    for spec in specs:
        result.update(spec)
    
    # Special handling for fields - merge instead of replace
    all_fields = []
    field_names = set()
    
    for spec in specs:
        for field in spec.get('fields', []):
            if field['name'] not in field_names:
                all_fields.append(field)
                field_names.add(field['name'])
    
    result['fields'] = all_fields
    return result