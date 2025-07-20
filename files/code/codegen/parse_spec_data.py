import json

# Parse the spec data from validation output
if isinstance(raw_data, dict) and 'data' in raw_data:
    spec = raw_data['data']
elif isinstance(raw_data, str):
    spec = json.loads(raw_data)
else:
    spec = raw_data

# Prepare context for templates
result = {
    'spec': spec,
    'nodeType': spec['nodeType'],
    'displayName': spec.get('displayName', spec['nodeType']),
    'fields': spec.get('fields', []),
    'handles': spec.get('handles', {}),
    'category': spec.get('category', 'custom'),
    'icon': spec.get('icon', '📦'),
    'color': spec.get('color', '#6b7280'),
    'description': spec.get('description', '')
}

# Convert Python booleans to JavaScript format for templates
for field in result['fields']:
    if 'required' in field:
        field['required'] = 'true' if field['required'] else 'false'
    if 'defaultValue' in field:
        if isinstance(field['defaultValue'], str):
            field['defaultValue'] = f"'{field['defaultValue']}'"
        elif field['defaultValue'] is None:
            field['defaultValue'] = 'null'

print(f"Parsed spec for node type: {result['nodeType']}")