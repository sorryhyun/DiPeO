# Template Job Integration Strategy

## Overview

Instead of modifying individual code generators, we can enhance the `template_job` node to use our new service layer. This provides a clean integration point that:

1. Maintains backward compatibility
2. Works within the diagram execution constraints
3. Provides opt-in enhancements

## Key Integration Points

### 1. Enhanced Template Engines

Add support for enhanced template rendering in `template_job.py`:

```python
# In template_job.py execute_request method
if engine == "jinja2":
    # Check if services are available
    if SERVICES_AVAILABLE:
        # Use TemplateService for enhanced rendering
        rendered = self._template_service.render_string(template_content, **template_vars)
    else:
        # Fall back to standard Jinja2
        rendered = await self._render_jinja2(template_content, template_vars)
```

### 2. Variable Preprocessing

Before rendering, enrich template variables with type information:

```python
def _preprocess_template_vars(self, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich variables with type projections."""
    if not SERVICES_AVAILABLE:
        return variables
    
    # For each field with type information
    if 'fields' in variables:
        for field in variables['fields']:
            if 'type' in field:
                # Parse type and add projections
                expr = self._type_algebra.parse(field['type'])
                field['type_projections'] = {
                    'python': self._type_algebra.project(expr, 'python'),
                    'typescript': self._type_algebra.project(expr, 'typescript'),
                    'graphql': self._type_algebra.project(expr, 'graphql')
                }
    
    return variables
```

### 3. Modified Diagram Flow

Update code generation diagrams to use template_job nodes:

```yaml
# Before: Direct code_job node
- label: Generate Enums
  type: code_job
  props:
    language: python
    filePath: files/codegen/code/models/generate_enums/enums_generator.py
    functionName: generate_enums

# After: Template job with preprocessing
- label: Generate Enums
  type: template_job
  props:
    engine: jinja2  # Automatically enhanced when services available
    template_path: files/codegen/templates/models/enums.j2
    output_path: dipeo/diagram_generated_staged/enums.py
```

## Benefits

1. **No Breaking Changes**: Existing diagrams continue to work
2. **Gradual Adoption**: Can migrate one generator at a time
3. **Automatic Enhancement**: When services are available, templates get:
   - All shared filters (snake_case, camel_case, etc.)
   - Type projections (python_type, graphql_type, etc.)
   - Macro support
   - Better error messages

4. **Simpler Generators**: Code generators become pure data extractors:
   ```python
   def extract_enums(inputs):
       # Just extract and return data
       return {'enums': [...]}
   ```

## Migration Example

### Step 1: Simplify the Generator

```python
# enums_extractor.py (renamed from enums_generator.py)
def extract_enums(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract enum data from AST."""
    ast_data = inputs.get('ast_data', {})
    
    enums = []
    for enum in ast_data.get('enums', []):
        enums.append({
            'name': enum.get('name'),
            'values': enum.get('members', []),
            'description': enum.get('description', '')
        })
    
    return {'enums': enums}
```

### Step 2: Update the Diagram

```yaml
nodes:
  # Extract data
  - label: Extract Enums
    type: code_job
    props:
      language: python
      filePath: files/codegen/code/models/enums_extractor.py
      functionName: extract_enums

  # Render with template_job
  - label: Generate Enums
    type: template_job
    props:
      engine: jinja2
      template_path: files/codegen/templates/models/enums.j2
      output_path: dipeo/diagram_generated_staged/enums.py

connections:
  - from: Extract Enums
    to: Generate Enums
    label: enums  # Pass extracted data as 'enums' variable
```

### Step 3: Update Templates

Templates can now use enhanced features when available:

```jinja2
{# enums.j2 - works with both standard and enhanced rendering #}
from enum import Enum

{% for enum in enums %}
class {{ enum.name }}(Enum):
    """{{ enum.description }}"""
    {% for value in enum['values'] %}  {# Use bracket notation #}
    {{ value.name }} = "{{ value.name }}"
    {% endfor %}
{% endfor %}
```

## Implementation Checklist

1. [ ] Add service imports to template_job.py (with try/except guard)
2. [ ] Enhance _render_jinja2 method to check for services
3. [ ] Add _preprocess_template_vars method
4. [ ] Update existing diagrams to use template_job nodes
5. [ ] Simplify generators to be pure data extractors
6. [ ] Test with and without services available

## Future Enhancements

1. **Custom Engines**: Add "jinja2-enhanced" as explicit engine choice
2. **Type Checking**: Validate template variables against expected types
3. **Caching**: Cache preprocessed variables for repeated renders
4. **Debugging**: Add debug mode showing type projections