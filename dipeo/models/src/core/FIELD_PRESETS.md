# Field Presets Documentation

This document describes the reusable field presets available in `field-presets.ts` for creating consistent node specifications across DiPeO.

## Overview

Field presets are factory functions that generate `FieldSpecification` objects with common, reusable configurations. They reduce duplication, ensure consistency, and make node specs more maintainable.

## Benefits

1. **DRY Principle**: Eliminate duplicate field definitions across specs
2. **Consistency**: Ensure UI behavior and validation are uniform
3. **Maintainability**: Update common patterns in one place
4. **Type Safety**: Full TypeScript support with intellisense
5. **Customization**: Override any property while keeping sensible defaults

## Available Presets

### AI & LLM Related

#### `personField()`
Creates a person/agent selection field.

```ts
import { personField } from '../core/field-presets.js';

// Basic usage
personField()

// With customization
personField({
  name: 'judge_person',
  description: 'AI agent to use for decision making',
  required: true
})
```

#### `promptWithFileField()`
Creates a pair of fields: textarea for inline prompts + hidden file path field.

```ts
import { promptWithFileField } from '../core/field-presets.js';

// Basic usage (returns 2 fields)
...promptWithFileField()

// Customized
...promptWithFileField({
  name: 'system_prompt',
  fileFieldName: 'system_prompt_file',
  description: 'System prompt template',
  placeholder: 'You are a helpful assistant...',
  rows: 8,
  column: 1,
  required: true
})

// With conditional display
...promptWithFileField({
  name: 'judge_by',
  fileFieldName: 'judge_by_file',
  conditionalConfig: {
    field: 'condition_type',
    values: [ConditionType.LLM_DECISION]
  }
})
```

#### `memoryControlFields()`
Creates fields for AI memory/context management.

```ts
import { memoryControlFields } from '../core/field-presets.js';

// Basic usage (returns 2 fields: memorize_to, at_most)
...memoryControlFields()

// With all options
...memoryControlFields({
  includeIgnorePerson: true,  // Adds ignore_person field
  defaultMemorizeTo: 'GOLDFISH',
  maxAtMost: 500
})
```

### Batch Processing

#### `batchExecutionFields()`
Creates fields for batch processing configuration.

```ts
import { batchExecutionFields } from '../core/field-presets.js';

// Basic usage (returns 4 fields)
...batchExecutionFields()

// Customized
...batchExecutionFields({
  defaultBatchInputKey: 'tasks',
  defaultMaxConcurrent: 5,
  maxConcurrentLimit: 50
})
```

### File & Content Management

#### `filePathField()`
Creates a file path input field.

```ts
import { filePathField } from '../core/field-presets.js';

filePathField({
  name: 'template_path',
  description: 'Path to template file',
  placeholder: '/templates/example.j2',
  required: false
})
```

#### `contentField()`
Creates an inline content field (textarea or code editor).

```ts
import { contentField } from '../core/field-presets.js';

// Textarea variant
contentField({
  name: 'template_content',
  description: 'Inline template content',
  placeholder: 'Enter template...',
  rows: 10,
  inputType: 'textarea'
})

// Code editor variant
contentField({
  name: 'code',
  description: 'Inline code to execute',
  inputType: 'code',
  language: SupportedLanguage.PYTHON,
  rows: 15
})
```

#### `fileOrContentFields()`
Creates a pair of fields for file path OR inline content.

```ts
import { fileOrContentFields } from '../core/field-presets.js';

// Basic usage (returns 2 fields)
...fileOrContentFields()

// Customized for code
...fileOrContentFields({
  fileFieldName: 'script_path',
  contentFieldName: 'script_code',
  fileDescription: 'Path to Python script',
  contentDescription: 'Inline Python code',
  contentInputType: 'code',
  language: SupportedLanguage.PYTHON,
  rows: 12
})
```

### Common Fields

#### `timeoutField()`
Creates a timeout configuration field.

```ts
import { timeoutField } from '../core/field-presets.js';

// Default (0-3600 seconds)
timeoutField()

// Customized
timeoutField({
  name: 'request_timeout',
  description: 'API request timeout in seconds',
  defaultValue: 30,
  min: 5,
  max: 300,
  required: true
})
```

#### `booleanField()`
Creates a boolean checkbox field.

```ts
import { booleanField } from '../core/field-presets.js';

booleanField({
  name: 'serialize_json',
  description: 'Serialize structured data to JSON string',
  defaultValue: false,
  required: false
})
```

#### `numberField()`
Creates a number input field with validation.

```ts
import { numberField } from '../core/field-presets.js';

numberField({
  name: 'max_iteration',
  description: 'Maximum execution iterations',
  defaultValue: 100,
  min: 1,
  max: 1000,
  required: true
})
```

#### `textField()`
Creates a text input field.

```ts
import { textField } from '../core/field-presets.js';

textField({
  name: 'collection',
  description: 'Database collection name',
  placeholder: 'my_collection',
  required: false,
  column: 1
})
```

#### `enumSelectField()`
Creates an enum selection dropdown field.

```ts
import { enumSelectField } from '../core/field-presets.js';
import { HttpMethod } from '../core/enums/node-specific.js';

enumSelectField({
  name: 'method',
  description: 'HTTP method',
  options: [
    { value: HttpMethod.GET, label: 'GET' },
    { value: HttpMethod.POST, label: 'POST' },
    { value: HttpMethod.PUT, label: 'PUT' }
  ],
  defaultValue: HttpMethod.GET,
  required: true,
  allowedValues: ['GET', 'POST', 'PUT']
})
```

#### `objectField()`
Creates an object/code editor field for structured data.

```ts
import { objectField } from '../core/field-presets.js';

objectField({
  name: 'headers',
  description: 'HTTP headers',
  required: false,
  collapsible: true
})
```

## Complete Example

Here's a before/after comparison showing how presets simplify node specs:

### Before (Original)

```ts
export const personJobSpec: NodeSpecification = {
  // ... metadata ...
  fields: [
    {
      name: "person",
      type: "PersonID",
      required: false,
      description: "AI person to use",
      uiConfig: {
        inputType: "personSelect"
      }
    },
    {
      name: "default_prompt",
      type: "string",
      required: false,
      description: "Default prompt template",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template...",
        column: 2,
        rows: 10,
        adjustable: true,
        showPromptFileButton: true
      }
    },
    {
      name: "prompt_file",
      type: "string",
      required: false,
      description: "Path to prompt file in /files/prompts/",
      uiConfig: {
        inputType: "text",
        placeholder: "example.txt",
        column: 2,
        hidden: true
      }
    },
    {
      name: "max_iteration",
      type: "number",
      required: true,
      defaultValue: 100,
      description: "Maximum execution iterations",
      uiConfig: {
        inputType: "number",
        min: 1
      }
    },
    {
      name: "memorize_to",
      type: "string",
      required: false,
      description: "Criteria used to select helpful messages for this task...",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., requirements, acceptance criteria",
        column: 2
      }
    },
    {
      name: "at_most",
      type: "number",
      required: false,
      description: "Select at most N messages to keep...",
      validation: {
        min: 1,
        max: 500
      },
      uiConfig: {
        inputType: "number",
        min: 1,
        max: 500,
        column: 1
      }
    },
    {
      name: "ignore_person",
      type: "string",
      required: false,
      description: "Comma-separated list of person IDs...",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., assistant, user2",
        column: 2
      }
    },
    // ... more fields ...
  ]
};
```

### After (With Presets)

```ts
import {
  personField,
  promptWithFileField,
  numberField,
  memoryControlFields,
  batchExecutionFields
} from '../core/field-presets.js';

export const personJobSpec: NodeSpecification = {
  // ... metadata ...
  fields: [
    personField(),
    ...promptWithFileField(),
    numberField({
      name: 'max_iteration',
      description: 'Maximum execution iterations',
      defaultValue: 100,
      min: 1,
      required: true
    }),
    ...memoryControlFields({ includeIgnorePerson: true }),
    // ... other custom fields ...
    ...batchExecutionFields()
  ]
};
```

## Best Practices

### 1. Use Spread Operator for Multi-Field Presets

Some presets return multiple fields. Use the spread operator to include them:

```ts
fields: [
  ...promptWithFileField(),  // Returns 2 fields
  ...memoryControlFields(),  // Returns 2-3 fields
  ...batchExecutionFields()  // Returns 4 fields
]
```

### 2. Customize When Needed

All presets accept options for customization:

```ts
personField({
  name: 'reviewer',
  description: 'AI reviewer to validate output',
  required: true
})
```

### 3. Combine Presets and Custom Fields

Mix presets with custom field definitions:

```ts
fields: [
  personField(),
  ...promptWithFileField(),
  // Custom field specific to this node
  {
    name: 'special_mode',
    type: 'string',
    required: false,
    description: 'Special processing mode',
    uiConfig: {
      inputType: 'text'
    }
  },
  ...memoryControlFields()
]
```

### 4. Override Any Property

Use the override parameter or options to change any aspect:

```ts
// Override any property
personField({
  required: true,
  description: 'Required AI agent',
  uiConfig: {
    inputType: 'personSelect',
    placeholder: 'Select an agent'
  }
})
```

## Migration Guide

To migrate existing node specs to use presets:

1. **Identify Common Patterns**: Look for fields that match preset patterns
2. **Import Presets**: Add imports for relevant presets
3. **Replace Fields**: Replace manual field definitions with preset calls
4. **Test**: Run codegen to verify generated code is correct
5. **Review**: Check UI behavior in frontend

## Adding New Presets

When adding a new preset:

1. Identify the common pattern across 2+ specs
2. Create a factory function with sensible defaults
3. Add customization options via parameters
4. Document with JSDoc comments and examples
5. Update this documentation

## Related Files

- `field-presets.ts` - Preset implementations
- `node-specification.ts` - Type definitions
- `../nodes/*.spec.ts` - Node specifications that use presets

## Future Enhancements

Potential improvements to the preset system:

- [ ] Validation preset builders
- [ ] Conditional field group presets
- [ ] GraphQL-specific field presets
- [ ] Integration-specific presets (Auth, API, etc.)
