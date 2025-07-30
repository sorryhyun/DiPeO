# Code Generation Migration Guide

This guide explains how to migrate existing generators to use the new service layer while maintaining diagram compatibility.

## Key Principle: Separation of Concerns

The migration follows a crucial architectural principle:
- **Diagram-callable functions** remain simple and data-driven (dict in, dict out)
- **Service layer** is used for pre-processing, type conversion, and template enhancement
- **No complex dependencies** in code that runs within diagram execution

## Migration Pattern

### 1. Keep the Original Interface

```python
# Original function signature - DO NOT CHANGE
def generate_something(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Called by diagram nodes - must remain data-driven."""
    template_content = inputs.get('template_content', '')
    data = inputs.get('data', {})
    
    # Simple processing only - no service imports here
    generated_code = render_simple(template_content, data)
    
    return {
        'generated_code': generated_code,
        'filename': 'output.py'
    }
```

### 2. Create a Preprocessor Using Services

```python
# New file: something_preprocessor.py
from files.codegen.code.services import (
    CoreTypeAlgebra,
    ASTService, 
    TemplateService
)

class SomethingPreprocessor:
    """Uses services for heavy lifting - runs OUTSIDE diagram execution."""
    
    def __init__(self):
        self.type_algebra = CoreTypeAlgebra()
        self.ast_service = ASTService()
        self.template_service = TemplateService()
    
    def prepare_data(self, source_files: List[str]) -> dict:
        """Process source files and prepare data package."""
        # Use AST service for parsing
        # Use type algebra for type conversion
        # Return simple dict that can be serialized
        return {
            'template_content': '...',
            'data': {...}  # Simple, serializable data
        }
```

### 3. Dual Rendering Support

```python
# In the generator module
def render_template_inline(template_content: str, context: dict) -> str:
    """Fallback rendering for diagram execution."""
    try:
        # Try Jinja2 if available
        from jinja2 import Template
        return Template(template_content).render(**context)
    except:
        # Ultra-simple fallback
        return template_content

def render_template_with_services(template_content: str, context: dict) -> str:
    """Enhanced rendering using services - for direct Python usage."""
    template_service = TemplateService()
    return template_service.render_string(template_content, **context)
```

## Migration Checklist

1. ✅ Create `*_v2.py` version of generator
2. ✅ Maintain original function signatures for diagram compatibility
3. ✅ Create `*_preprocessor.py` for service-based processing
4. ✅ Use bracket notation `item['field']` instead of dot notation in templates
5. ✅ Test both diagram execution and direct Python usage
6. ✅ Document any template syntax changes needed

## Common Gotchas

### 1. Jinja2 Dict Access
```jinja2
{# Wrong - conflicts with dict.values() method #}
{% for value in enum.values %}

{# Correct - use bracket notation #}
{% for value in enum['values'] %}
```

### 2. Import Guards
```python
# Always guard service imports
try:
    from files.codegen.code.services import TemplateService
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
```

### 3. Data Serialization
```python
# Ensure all data is JSON-serializable
package = {
    'template_content': str,  # Not Path objects
    'data': dict,             # Not custom classes
    'metadata': dict          # Simple types only
}
```

## Example: Enums Generator Migration

See the complete example in:
- `/files/codegen/code/models/generate_enums/enums_generator_v2.py` - Migrated generator
- `/files/codegen/code/models/generate_enums/enums_preprocessor.py` - Service-based preprocessor
- `/files/codegen/code/models/generate_enums/test_migration.py` - Tests

## Benefits of This Approach

1. **Backward Compatibility**: Existing diagrams continue to work
2. **No Runtime Dependencies**: Diagram execution remains lightweight
3. **Enhanced Capabilities**: Direct Python usage gets full service benefits
4. **Gradual Migration**: Can migrate one generator at a time
5. **Type Safety**: Services provide better type checking and validation

## Next Steps

1. Identify generators that would benefit most from services
2. Create preprocessors for complex type conversions
3. Update templates to use bracket notation where needed
4. Test thoroughly with both diagram and direct execution
5. Document any breaking changes in templates