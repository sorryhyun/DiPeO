"""
Helper functions for the spec_ingestion diagram.
Handles node specification parsing, normalization, and metadata addition.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any


def normalize_spec_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw spec into canonical spec_data structure"""
    spec = inputs.get('validated_spec', {})
    
    # Extract base info
    node_type = spec.get('nodeType', 'unknown')
    display_name = spec.get('displayName', node_type.replace('_', ' ').title())
    
    # Convert to camelCase and other formats
    camel_case = ''.join(word.capitalize() if i > 0 else word.lower() 
                        for i, word in enumerate(node_type.split('_')))
    pascal_case = ''.join(word.capitalize() for word in node_type.split('_'))
    
    # Build canonical spec_data
    spec_data = {
        'nodeType': node_type,
        'displayName': display_name,
        'camelCase': camel_case,
        'pascalCase': pascal_case,
        'description': spec.get('description', ''),
        'category': spec.get('category', 'Other'),
        'icon': spec.get('icon', 'default'),
        'fields': spec.get('fields', []),
        'handles': spec.get('handles', {
            'inputs': [{'label': 'default', 'dataType': 'any'}],
            'outputs': [{'label': 'default', 'dataType': 'any'}]
        }),
        'validation': spec.get('validation', {}),
        'defaults': spec.get('defaults', {}),
        'rawSpec': spec
    }
    
    # Add computed fields
    spec_data['hasInputs'] = len(spec_data['handles'].get('inputs', [])) > 0
    spec_data['hasOutputs'] = len(spec_data['handles'].get('outputs', [])) > 0
    spec_data['fieldCount'] = len(spec_data['fields'])
    
    # Ensure all fields have required properties
    for field in spec_data['fields']:
        field.setdefault('required', False)
        field.setdefault('defaultValue', None)
        field.setdefault('description', '')
        field.setdefault('validation', {})
        
    return {'spec_data': spec_data}


def add_generation_metadata(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Add generation metadata to the spec data"""
    spec_data = inputs.get('spec_data', {})
    
    # Add generation metadata
    spec_data['_metadata'] = {
        'generatedAt': datetime.utcnow().isoformat(),
        'generatorVersion': '2.0.0',
        'specFile': inputs.get('spec_path', 'unknown'),
        'environment': {
            'python_version': os.sys.version.split()[0],
            'platform': os.sys.platform
        }
    }
    
    return {'spec_data': spec_data}