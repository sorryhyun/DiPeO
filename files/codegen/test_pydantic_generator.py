#!/usr/bin/env python3
"""Test script for pydantic generator with minimal data."""

import json
import os
import sys
from pathlib import Path

# Set DIPEO_BASE_DIR to project root
os.environ['DIPEO_BASE_DIR'] = str(Path(__file__).parent.parent.parent)

# Add codegen code to path
code_path = str(Path(__file__).parent / 'code')
sys.path.insert(0, code_path)

# Import directly
from code.generators.pydantic_generator import generate_pydantic_models

# Create minimal test data
test_model_data = {
    "imports": [
        {"module": "typing", "items": ["Any", "Dict", "Optional"], "is_type_import": True},
        {"module": "enum", "items": ["Enum"], "is_type_import": False},
        {"module": "pydantic", "items": ["BaseModel", "Field"], "is_type_import": False}
    ],
    "type_aliases": {
        "NodeID": "str",
        "PersonID": "str"
    },
    "enums": [
        {"name": "TestEnum"}
    ],
    "models": [
        {
            "name": "TestEnum",
            "type": "enum",
            "bases": ["str", "Enum"],
            "enum_values": [
                ["VALUE1", "value1"],
                ["VALUE2", "value2"]
            ],
            "docstring": "Test enumeration"
        },
        {
            "name": "TestModel",
            "type": "class", 
            "bases": ["BaseModel"],
            "docstring": "Test model class",
            "fields": {
                "id": {
                    "name": "id",
                    "type": "str",
                    "required": True,
                    "field_definition": None
                },
                "label": {
                    "name": "label",
                    "type": "str", 
                    "required": False,
                    "field_definition": "Field(default=None)"
                },
                "count": {
                    "name": "count",
                    "type": "int",
                    "required": False,
                    "field_definition": "Field(default=0)"
                }
            },
            "methods": []
        },
        {
            "name": "TestNode",
            "type": "class",
            "bases": ["BaseModel"],
            "docstring": "Test node class",
            "fields": {
                "type": {
                    "name": "type",
                    "type": "str",
                    "required": True,
                    "field_definition": None
                }
            },
            "methods": []
        }
    ]
}

# Save model data to temporary location
print("Saving test model data...")
temp_dir = Path('.temp/codegen')
temp_dir.mkdir(parents=True, exist_ok=True)
model_data_file = temp_dir / 'model_data.json'

with open(model_data_file, 'w') as f:
    json.dump(test_model_data, f, indent=2)
print(f"Saved model data to {model_data_file}")

# First test with debug template
print("\nTesting with debug template...")
from jinja2 import Environment, FileSystemLoader
template_dir = Path(os.environ['DIPEO_BASE_DIR']) / 'files' / 'codegen' / 'templates' / 'backend'
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template('pydantic_models_debug.j2')

try:
    debug_content = template.render(model_data=test_model_data)
    print("Debug output:")
    print(debug_content)
except Exception as e:
    print(f"Debug template error: {e}")

# Test generate_pydantic_models
print("\nTesting generate_pydantic_models...")
result = generate_pydantic_models({})

if 'error' in result:
    print(f"Error: {result['error']}")
else:
    print(f"Success! Generated: {result['path']}")
    
    # Read and display generated content
    with open(result['path'], 'r') as f:
        content = f.read()
    
    print("\nGenerated content preview (first 50 lines):")
    lines = content.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}: {line}")
    
    # Check for Handlebars syntax
    if '{{' in content or '}}' in content:
        print("\n⚠️  WARNING: Generated content still contains Handlebars syntax!")
    else:
        print("\n✅ No Handlebars syntax found in generated content")