"""Test the migrated enums generator."""

import json
import sys
import os

# Add parent path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enums_generator_v2 import generate_enums, render_template_inline


def test_inline_rendering():
    """Test inline template rendering (no dependencies)."""
    # Test if Jinja2 works directly
    try:
        from jinja2 import Template
        print("Jinja2 import successful in test")
        test_template = Template("Hello {{ name }}")
        test_result = test_template.render(name="World")
        print(f"Jinja2 test render: {test_result}")
    except ImportError as e:
        print(f"Jinja2 import failed in test: {e}")
    
    template = """# Generated Enums
{% for enum in enums %}
class {{ enum.name }}(Enum):
    {% for value in enum['values'] %}
    {{ value.name }} = "{{ value.name }}"
    {% endfor %}
{% endfor %}"""
    
    enums_data = [
        {
            'name': 'NodeType',
            'values': [
                {'name': 'INPUT', 'value': 'INPUT'},
                {'name': 'OUTPUT', 'value': 'OUTPUT'},
                {'name': 'PROCESS', 'value': 'PROCESS'}
            ]
        },
        {
            'name': 'MemoryProfile',
            'values': [
                {'name': 'DEFAULT', 'value': 'DEFAULT'},
                {'name': 'EXTENDED', 'value': 'EXTENDED'},
                {'name': 'MINIMAL', 'value': 'MINIMAL'}
            ]
        }
    ]
    
    result = render_template_inline(template, {'enums': enums_data})
    print("Inline rendering result:")
    print(result)
    print("-" * 50)
    
    # Debug: check data structure
    print("Enums data structure:")
    for enum in enums_data:
        print(f"  Enum: {enum['name']}")
        print(f"  Values type: {type(enum.get('values'))}")
        print(f"  Values: {enum.get('values')}")
    
    # Verify content
    assert 'class NodeType(Enum):' in result
    assert 'INPUT = "INPUT"' in result
    assert 'class MemoryProfile(Enum):' in result
    assert 'DEFAULT = "DEFAULT"' in result


def test_diagram_interface():
    """Test the data-driven interface for diagrams."""
    # Simulate diagram node inputs
    inputs = {
        'template_content': """from enum import Enum

{% for enum in enums %}
class {{ enum.name }}(Enum):
    \"\"\"{{ enum.description }}\"\"\"
    {% for value in enum['values'] %}
    {{ value.name }} = "{{ value.name }}"
    {% endfor %}

{% endfor %}""",
        'enums_data': json.dumps([
            {
                'name': 'DiagramFormat',
                'description': 'Supported diagram formats',
                'values': [
                    {'name': 'LIGHT', 'value': 'LIGHT'},
                    {'name': 'NATIVE', 'value': 'NATIVE'}
                ]
            }
        ])
    }
    
    # Call the diagram interface
    result = generate_enums(inputs)
    
    print("Diagram interface result:")
    print(result['generated_code'])
    print(f"Filename: {result['filename']}")
    print("-" * 50)
    
    # Verify output
    assert 'generated_code' in result
    assert 'filename' in result
    assert result['filename'] == 'enums.py'
    assert 'class DiagramFormat(Enum):' in result['generated_code']
    assert 'Supported diagram formats' in result['generated_code']


def test_services_integration():
    """Test service-based generation (when available)."""
    try:
        from enums_generator_v2 import generate_enums_with_services
        
        template = """from enum import Enum
from typing import Dict

{% for enum in enums %}
class {{ enum.name | pascal_case }}(Enum):
    {% for value in enum.values %}
    {{ value.name | upper }} = "{{ value.name | lower }}"
    {% endfor %}
{% endfor %}"""
        
        enums_data = [
            {
                'name': 'hook_type',
                'values': [
                    {'name': 'before_execution'},
                    {'name': 'after_execution'}
                ]
            }
        ]
        
        result = generate_enums_with_services(template, enums_data)
        print("Service-based generation result:")
        print(result)
        print("-" * 50)
        
    except ImportError:
        print("Services not available - skipping service integration test")


if __name__ == '__main__':
    print("Testing migrated enums generator...")
    print("=" * 50)
    
    test_inline_rendering()
    test_diagram_interface()
    test_services_integration()
    
    print("\nAll tests passed! ✓")