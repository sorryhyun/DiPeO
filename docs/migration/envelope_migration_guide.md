# Migration Guide: StandardNodeOutput to Envelope Pattern

## Overview

This guide helps you migrate from the deprecated `StandardNodeOutput` class to the new `Envelope` pattern with multi-representation support.

**Timeline**: StandardNodeOutput will be maintained for 2 release cycles (until Q2 2025) before removal.

## Why Migrate?

The new Envelope pattern provides:
- **Multiple representations**: Same data in different formats (text, object, etc.)
- **Better type safety**: ContentType-aware transformations
- **Cleaner API**: No more forced conversions between formats
- **Performance**: Avoid redundant serialization/deserialization

## Quick Migration Examples

### Before (StandardNodeOutput)

```python
from dipeo.domain.diagram.models.executable_diagram import StandardNodeOutput

class MyHandler(BaseJobHandler):
    def serialize_output(self, result, request):
        # Old way: Using StandardNodeOutput
        return StandardNodeOutput.from_value({
            "result": result.data,
            "status": "success"
        })
```

### After (Envelope with Representations)

```python
from dipeo.domain.execution.envelope import EnvelopeFactory

class MyHandler(BaseJobHandler):
    def serialize_output(self, result, request):
        # New way: Using Envelope with representations
        data = {"result": result.data, "status": "success"}
        
        envelope = EnvelopeFactory.json(data)
        envelope = envelope.with_representations({
            "text": f"Result: {result.data}",
            "object": data,
            "summary": f"Processed {len(result.data)} items"
        })
        
        return envelope
```

## Migration Patterns

### Pattern 1: Simple Value Output

**Before:**
```python
return StandardNodeOutput.from_value("Hello World")
```

**After:**
```python
return EnvelopeFactory.text("Hello World")
```

### Pattern 2: Structured Data Output

**Before:**
```python
return StandardNodeOutput.from_dict({
    "value": data,
    "outputs": {"default": data, "summary": summary},
    "metadata": {"timestamp": now}
})
```

**After:**
```python
envelope = EnvelopeFactory.json(data)
envelope = envelope.with_representations({
    "text": str(data),
    "object": data,
    "summary": summary
})
envelope = envelope.with_meta(timestamp=now)
return envelope
```

### Pattern 3: Multiple Output Formats

**Before (workaround with duplicated nodes):**
```yaml
# Had to create separate nodes for text/object outputs
- id: process_text
  type: code_job
  data:
    code: return str(data)
    
- id: process_object  
  type: code_job
  data:
    code: return data
```

**After (single node with representations):**
```python
def serialize_output(self, result, request):
    envelope = EnvelopeFactory.json(result)
    envelope = envelope.with_representations({
        "text": str(result),  # For text consumers
        "object": result,     # For object consumers
        "markdown": format_as_markdown(result)  # Custom format
    })
    return envelope
```

## Handler Migration Checklist

For each handler using StandardNodeOutput:

1. ✅ **Remove StandardNodeOutput imports**
   ```python
   # Remove this:
   from dipeo.domain.diagram.models.executable_diagram import StandardNodeOutput
   
   # Add this:
   from dipeo.domain.execution.envelope import EnvelopeFactory
   ```

2. ✅ **Replace StandardNodeOutput creation**
   - Change `StandardNodeOutput.from_value()` → `EnvelopeFactory.text()` or `.json()`
   - Change `StandardNodeOutput.from_dict()` → `EnvelopeFactory.json()`

3. ✅ **Add representations for multiple formats**
   ```python
   envelope = envelope.with_representations({
       "text": text_version,
       "object": object_version,
       # Add custom representations as needed
   })
   ```

4. ✅ **Update metadata handling**
   ```python
   # Old: metadata dict
   StandardNodeOutput(value=x, metadata={"key": "value"})
   
   # New: with_meta() method
   envelope.with_meta(key="value")
   ```

## Common Representations

Standard representation keys used across DiPeO:

| Key | Purpose | Example |
|-----|---------|---------|
| `text` | Plain text representation | `"User John created"` |
| `object` | Structured data | `{"id": 123, "name": "John"}` |
| `markdown` | Formatted markdown | `"**User** _John_ created"` |
| `html` | HTML representation | `"<b>User</b> John"` |
| `summary` | Brief summary | `"1 user created"` |
| `conversation` | Conversation state | `[Message(...), ...]` |
| `sql` | SQL representation | `"SELECT * FROM users"` |

## Edge Content Type Handling

The new system automatically selects the right representation based on edge `content_type`:

```yaml
# In your diagram
edges:
  - source: api_job_1
    target: template_job_1
    content_type: raw_text  # Will use "text" representation
    
  - source: api_job_1
    target: code_job_1
    content_type: object    # Will use "object" representation
```

## Testing Your Migration

1. **Enable deprecation warnings**:
   ```python
   import warnings
   warnings.simplefilter('always', DeprecationWarning)
   ```

2. **Run your tests** and fix any deprecation warnings

3. **Verify edge extraction** works correctly:
   ```python
   # The system will log when using representations
   # Check logs for: "Using 'text' representation for edge..."
   ```

## Backward Compatibility

During the migration period:
- ✅ Existing StandardNodeOutput code continues to work
- ✅ Deprecation warnings guide migration
- ✅ Mixed usage (some handlers migrated, others not) is supported
- ✅ Edge extraction handles both patterns transparently

## Getting Help

- Check handler examples in `/dipeo/application/execution/handlers/`
- See the technical design in `/docs/architecture/multi_representation_pattern.md`
- Review Part 1 and Part 2 implementation docs for context

## Timeline

- **Now - Q1 2025**: Migration period with deprecation warnings
- **Q1 2025**: Final migration push, enhanced tooling
- **Q2 2025**: StandardNodeOutput removal

---

**Last Updated**: 2025-09-03  
**Status**: Migration Support Active