#!/usr/bin/env python3
"""Test individual parts of the pydantic template."""

import json
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, DebugUndefined

# Set DIPEO_BASE_DIR to project root
os.environ['DIPEO_BASE_DIR'] = str(Path(__file__).parent.parent.parent)

# Test data
test_model_data = {
    "imports": [{"module": "typing", "items": ["Any"], "is_type_import": True}],
    "type_aliases": {"NodeID": "str"},
    "models": [{
        "name": "TestModel",
        "type": "class",
        "bases": ["BaseModel"],
        "fields": {
            "id": {"name": "id", "type": "str", "required": True}
        }
    }]
}

# Test template parts
template_parts = [
    ("imports", """
{% for import in model_data.imports %}
{{ import.module }} - {{ import.items|join(", ") }}
{% endfor %}
"""),
    ("type_aliases", """
{% for key, value in model_data.type_aliases.items() %}
{{ key }} = {{ value }}
{% endfor %}
"""),
    ("models", """
{% for model in model_data.models %}
Model: {{ model.name }}
{% endfor %}
"""),
    ("model_fields", """
{% for model in model_data.models %}
{% if model.fields %}
{% for field in model.fields.values() %}
Field: {{ field.name }}
{% endfor %}
{% endif %}
{% endfor %}
"""),
]

# Test each part
env = Environment(undefined=DebugUndefined)
for name, template_str in template_parts:
    print(f"\nTesting {name}:")
    try:
        template = env.from_string(template_str)
        result = template.render(model_data=test_model_data)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()