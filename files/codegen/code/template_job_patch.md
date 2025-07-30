# Minimal Patch for template_job.py

Here are the minimal changes needed to integrate the service layer into the existing `template_job.py`:

## 1. Add imports at the top (after existing imports)

```python
# Try to import enhanced services
try:
    from files.codegen.code.services import TemplateService
    TEMPLATE_SERVICE_AVAILABLE = True
except ImportError:
    TEMPLATE_SERVICE_AVAILABLE = False
```

## 2. Initialize service in __init__ method

```python
def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
    self._processor = TemplateProcessor()
    self.filesystem_adapter = filesystem_adapter
    
    # Initialize enhanced template service if available
    if TEMPLATE_SERVICE_AVAILABLE:
        self._template_service = TemplateService()
```

## 3. Modify the jinja2 rendering section in execute_request

Replace this section:
```python
elif engine == "jinja2":
    # Use Jinja2
    rendered = await self._render_jinja2(template_content, template_vars)
```

With:
```python
elif engine == "jinja2":
    # Use enhanced Jinja2 if available
    if TEMPLATE_SERVICE_AVAILABLE and hasattr(self, '_template_service'):
        try:
            rendered = self._template_service.render_string(template_content, **template_vars)
            request.add_metadata("enhanced_rendering", True)
        except Exception as e:
            # Fall back to standard Jinja2
            rendered = await self._render_jinja2(template_content, template_vars)
            request.add_metadata("enhancement_fallback", str(e))
    else:
        # Use standard Jinja2
        rendered = await self._render_jinja2(template_content, template_vars)
```

## That's it!

With just these three small changes:
1. Templates rendered with `engine: jinja2` automatically get enhanced features when services are available
2. All existing diagrams continue to work unchanged
3. Templates gain access to:
   - All shared filters (snake_case, camel_case, pascal_case, etc.)
   - Type conversion filters (python_type, graphql_type, etc.)
   - Enhanced error messages
   - Macro support

## Testing the Integration

Create a test diagram:
```yaml
nodes:
  - label: Test Data
    type: code_job
    props:
      language: python
      code: |
        return {
            'model_name': 'UserProfile',
            'fields': [
                {'name': 'user_id', 'type': 'string'},
                {'name': 'age', 'type': 'number'},
                {'name': 'tags', 'type': 'string[]'}
            ]
        }

  - label: Render with Template Job
    type: template_job
    props:
      engine: jinja2
      template_content: |
        class {{ model_name | snake_case }}:
            {% for field in fields %}
            {{ field.name }}: {{ field.type }}  # Could use | python_type filter if available
            {% endfor %}

connections:
  - from: Test Data
    to: Render with Template Job
```

When services are available, the `snake_case` filter will work. When not available, it will fail gracefully.