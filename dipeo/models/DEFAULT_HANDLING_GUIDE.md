# Default Value Handling Guide

## Overview

This guide documents default value handling across DiPeO's TypeScript specifications, code generation pipeline, and Python backend.

## Problem: Current Duplication

### Default Values Specified in Two Places

**1. TypeScript Specifications** (`/dipeo/models/src/nodes/*.spec.ts`)

```ts
{
  name: "batch",
  type: "boolean",
  required: false,
  defaultValue: false,  // ← Specified here
  description: "Enable batch mode"
}
```

**2. Code Generation Mappings** (`/dipeo/models/src/codegen/mappings.ts`)

```ts
export const FIELD_SPECIAL_HANDLING: Record<string, Record<string, any>> = {
  'sub_diagram': {
    'batch': { default: 'False' }  // ← And here (different syntax!)
  }
}
```

### Issues with Current Approach

1. **Duplication**: Same default specified in two places
2. **Inconsistency**: TypeScript uses `false`, Python uses `'False'`
3. **Maintenance Burden**: Must update both places when changing defaults
4. **Risk of Drift**: Easy for specs and generated code to get out of sync
5. **No Single Source of Truth**: Unclear which takes precedence

## Solution: Unified Default Handling

### Principle: TypeScript Specs as Single Source of Truth

**All default values should be specified once in TypeScript specifications.**

The code generation pipeline should infer Python defaults from TypeScript defaults automatically.

### New Utilities Created

#### 1. `default-value-utils.ts` - Default Value Management

```ts
import { createDefaultValue, DefaultValuePresets } from '../core/default-value-utils.js';

// Simple defaults
createDefaultValue(false)                    // Boolean
createDefaultValue("")                       // Empty string
createDefaultValue(100)                      // Number

// Enum defaults (auto-generates Python syntax)
createDefaultValue(HttpMethod.GET, {
  enumType: 'HttpMethod'
})  // → TS: HttpMethod.GET, Py: field(default=HttpMethod.GET)

// Complex defaults
createDefaultValue([], {
  description: 'Empty array of items'
})  // → TS: [], Py: field(default_factory=list)

// Using presets
DefaultValuePresets.emptyString()
DefaultValuePresets.emptyObject()
DefaultValuePresets.emptyArray()
DefaultValuePresets.false()
DefaultValuePresets.true()
DefaultValuePresets.number(100)
DefaultValuePresets.enum('HttpMethod', 'GET')
```

## Current State Analysis

### Default Values Across Specs

| Spec File | Fields with Defaults | Duplicate in FIELD_SPECIAL_HANDLING |
|-----------|---------------------|-------------------------------------|
| person-job.spec.ts | 5 (batch fields) | ❌ No (uses presets now) |
| api-job.spec.ts | 2 (url, method) | ✅ Yes - DUPLICATE |
| db.spec.ts | 4 (sub_type, operation, serialize_json, format) | ✅ Yes - DUPLICATE |
| code-job.spec.ts | 1 (language) | ✅ Yes - DUPLICATE |
| start.spec.ts | 3 (trigger_mode, custom_data, output_data_structure) | ✅ Yes - DUPLICATE |
| hook.spec.ts | 3 (hook_type, timeout, retries) | ✅ Yes - DUPLICATE |
| template-job.spec.ts | 1 (engine) | ✅ Yes - DUPLICATE |
| sub-diagram.spec.ts | 6 (batch fields, inherit, wait_mode) | ✅ Yes - DUPLICATE |
| condition.spec.ts | 2 (condition_type, memorize_to) | ✅ Yes - DUPLICATE |
| diff-patch.spec.ts | 4 (format, mode, verify, create_backup) | Partial - some duplicated |
| typescript-ast.spec.ts | 7 (extract_patterns, include_jsdoc, parse_mode, etc.) | ✅ Yes - DUPLICATE |
| integrated-api.spec.ts | 5 (provider, timeout, max_retries, config) | ✅ Yes - DUPLICATE |
| user-response.spec.ts | 2 (prompt, timeout) | ✅ Yes - DUPLICATE |

**Total Duplication**: ~40 default values specified in both places

## Recommended Patterns

### Pattern 1: Simple Defaults

Use the field's `defaultValue` property directly:

```ts
import { booleanField, numberField, textField } from '../core/field-presets.js';

booleanField({
  name: "batch",
  description: "Enable batch mode",
  defaultValue: false  // ← Single source of truth
})

numberField({
  name: "timeout",
  description: "Request timeout in seconds",
  defaultValue: 30,
  min: 1,
  max: 300
})

textField({
  name: "batch_input_key",
  description: "Key containing array to iterate",
  defaultValue: "items"
})
```

### Pattern 2: Enum Defaults

Specify enum defaults using enum values:

```ts
import { enumSelectField } from '../core/field-presets.js';
import { HttpMethod } from '../core/enums/node-specific.js';

enumSelectField({
  name: "method",
  description: "HTTP method",
  options: [
    { value: HttpMethod.GET, label: "GET" },
    { value: HttpMethod.POST, label: "POST" }
  ],
  defaultValue: HttpMethod.GET  // ← Enum default
})

// Code generation should infer:
// Python: field(default=HttpMethod.GET)
// GraphQL: default: GET
```

### Pattern 3: Complex Defaults (Objects/Arrays)

For objects and arrays, use factory functions:

```ts
// Empty object
{
  name: "custom_data",
  type: "object",
  required: false,
  defaultValue: {},  // ← Will generate: field(default_factory=dict)
  uiConfig: { inputType: "code" }
}

// Array with specific values
{
  name: "extract_patterns",
  type: "array",
  required: false,
  defaultValue: ["interface", "type", "enum"],  // ← Specific default array
  uiConfig: { inputType: "select" }
}
// Should generate: field(default_factory=lambda: ["interface", "type", "enum"])
```

## Migration Guide

### Step 1: Audit Current Defaults

Review `FIELD_SPECIAL_HANDLING` in `mappings.ts` and compare with spec defaults.

### Step 2: Update Specs to Include All Defaults

Ensure all defaults are specified in TypeScript specs:

```ts
// Before: Missing default in spec, only in FIELD_SPECIAL_HANDLING
{
  name: "timeout",
  type: "number",
  required: false,
  description: "Request timeout"
}

// After: Default in spec (single source of truth)
numberField({
  name: "timeout",
  description: "Request timeout",
  defaultValue: 30,
  min: 1,
  max: 300
})
```

### Step 3: Update Code Generation Pipeline

**Future Work (Week 4)**:

Modify the code generation pipeline to:

1. Read defaults from TypeScript specs
2. Use `inferPythonDefault()` to generate Python syntax
3. Remove `FIELD_SPECIAL_HANDLING` defaults (use only for truly special cases)

Example codegen logic:

```ts
// In IR builder or code generator
import { inferPythonDefault } from '../core/default-value-utils.js';

function generateFieldDefault(field: FieldSpecification): string {
  if (!field.defaultValue) {
    return 'None';
  }

  return inferPythonDefault(
    field.defaultValue,
    field.type,
    isEnumType(field.type) ? field.type : undefined
  );
}
```

### Step 4: Remove Duplicates from FIELD_SPECIAL_HANDLING

After codegen pipeline is updated, remove duplicate defaults:

```ts
// Before
export const FIELD_SPECIAL_HANDLING = {
  'api_job': {
    'url': { default: '""' },  // ← Remove (already in spec)
    'method': { default: 'field(default=HttpMethod.GET)' }  // ← Remove
  }
}

// After (only truly special handling remains)
export const FIELD_SPECIAL_HANDLING = {
  'person_job': {
    // Only keep special handling that can't be inferred from specs
    'memory_config': {
      special: 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None'
    }
  }
}
```

## Default Value Conversion Reference

| TypeScript Default | Python Default | GraphQL Default |
|-------------------|---------------|-----------------|
| `""` | `""` | `""` |
| `false` | `False` | `false` |
| `true` | `True` | `true` |
| `0` | `0` | `0` |
| `100` | `100` | `100` |
| `HttpMethod.GET` | `field(default=HttpMethod.GET)` | `GET` |
| `{}` | `field(default_factory=dict)` | `null` |
| `[]` | `field(default_factory=list)` | `null` |
| `["a", "b"]` | `field(default_factory=lambda: ["a", "b"])` | `null` |
| `{ "key": "value" }` | `field(default_factory=lambda: {"key": "value"})` | `null` |

## Testing Default Values

### Validation

Use the validation utility to ensure defaults match field types:

```ts
import { validateDefaultValue } from '../core/default-value-utils.js';

const result = validateDefaultValue(false, 'boolean');
if (!result.valid) {
  console.error(result.error);
}
```

### Codegen Test

After updating specs, test code generation:

```bash
cd dipeo/models && pnpm build
make codegen
make diff-staged  # Review generated Python defaults
```

## Best Practices

### 1. Always Specify Defaults in Specs

```ts
// ❌ Bad: No default (unclear what value to use)
{
  name: "timeout",
  type: "number",
  required: false
}

// ✅ Good: Explicit default
numberField({
  name: "timeout",
  description: "Request timeout",
  defaultValue: 30,
  min: 1,
  max: 300
})
```

### 2. Use Type-Appropriate Defaults

```ts
// ✅ Good: Boolean defaults
booleanField({ name: "enabled", defaultValue: false })

// ✅ Good: Enum defaults
enumSelectField({
  name: "format",
  options: [...],
  defaultValue: DataFormat.JSON
})

// ✅ Good: Empty object
objectField({ name: "config", defaultValue: {} })
```

### 3. Use Default Value Presets

```ts
import { DefaultValuePresets } from '../core/default-value-utils.js';

// Instead of manually specifying
{ defaultValue: false }

// Use preset
{ ...DefaultValuePresets.false() }

// Or for complex types
{ ...DefaultValuePresets.emptyObject() }
{ ...DefaultValuePresets.emptyArray() }
```

### 4. Document Unusual Defaults

```ts
numberField({
  name: "retries",
  description: "Number of retries (0 = no retries, useful for testing)",
  defaultValue: 0,  // Explicitly 0, not omitted
  min: 0,
  max: 10
})
```

## Future Enhancements

### Week 4 Migration Tasks

1. **Update Code Generation Pipeline**
   - Modify IR builders to read defaults from specs
   - Implement `inferPythonDefault()` in codegen
   - Remove redundant `FIELD_SPECIAL_HANDLING` entries

2. **Migrate All Specs**
   - Ensure all 16 specs have defaults specified
   - Validate default values match field types
   - Test generated code

3. **Remove Duplication**
   - Clean up `FIELD_SPECIAL_HANDLING`
   - Keep only truly special cases
   - Update documentation

### Validation Improvements

- [ ] Add runtime validation of defaults in specs
- [ ] Create spec validation test suite
- [ ] Add CI check for default consistency
- [ ] Generate migration report showing discrepancies

## Related Files

- `src/core/default-value-utils.ts` - Default value utilities
- `src/core/field-presets.ts` - Field presets (use these!)
- `src/codegen/mappings.ts` - Current FIELD_SPECIAL_HANDLING (to be cleaned up)
- `src/nodes/*.spec.ts` - Node specifications (single source of truth)

## Summary

**Current State**: ~40 default values duplicated across specs and mappings

**Solution**:
- ✅ Created default value utilities
- ✅ Documented patterns and best practices
- ✅ Provided migration guide
- 🔄 Week 4: Update codegen pipeline to use spec defaults

**Impact**:
- Single source of truth for defaults
- Reduced maintenance burden
- Eliminated risk of spec/codegen drift
- Clearer, more maintainable code
