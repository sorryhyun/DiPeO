# Node Configuration System

This directory contains configuration files for all DiPeO node types. The configuration system uses automatic field generation from domain models with UI-specific overrides.

## Architecture

### 1. Automatic Field Generation

Field configurations are automatically generated from the TypeScript domain models in `@dipeo/models`:

```bash
# Run from dipeo/models directory
pnpm generate:field-configs
```

This generates:
- `generated-fields.ts` - Base field configurations derived from domain model interfaces
- Field types, labels, and defaults are inferred from the TypeScript types

### 2. UI-Specific Overrides

The `fieldOverrides.ts` file allows customizing the generated fields without modifying the generation output:

```typescript
export const NODE_FIELD_OVERRIDES: FieldOverrides = {
  person_job: {
    excludeFields: ['person'], // Remove fields
    fieldOverrides: {
      tools: {
        placeholder: 'Custom placeholder' // Override properties
      }
    },
    additionalFields: [...], // Add UI-only fields
    fieldOrder: [...] // Custom field ordering
  }
};
```

### 3. Node Configuration Creation

Use the `createNodeConfig` helper to automatically merge generated fields with overrides:

```typescript
import { createNodeConfig } from './createNodeConfig';

export const MyNodeConfig = createNodeConfig<MyNodeData>({
  nodeType: 'my_node',
  label: 'My Node',
  icon: '📦',
  color: '#3b82f6',
  handles: { ... },
  defaults: { ... }
});
```

## Benefits

1. **Automatic synchronization**: New fields added to domain models automatically appear in the UI
2. **Type safety**: Field configurations are type-checked against domain models
3. **Customization**: UI-specific needs can be met without modifying generated code
4. **Maintainability**: Single source of truth for data structures

## Adding a New Node Type

1. Define the node data interface in `dipeo/models/src/diagram.ts`
2. Run `pnpm generate:field-configs` to generate base fields
3. Add any UI-specific overrides to `fieldOverrides.ts` if needed
4. Create the node config file using `createNodeConfig`

## Field Types

Available field types (from `FIELD_TYPES`):
- `text` - Single line text input
- `number` - Numeric input
- `checkbox` - Boolean checkbox
- `select` - Dropdown selection
- `textarea` - Multi-line text
- `personSelect` - Person entity selector
- `variableTextArea` - Text area with variable support
- `maxIteration` - Special number input for iterations
- `labelPersonRow` - Combined label and person selector
- `row` - Layout row container
- `custom` - Custom field component

## Directory Structure

```
nodes/
├── generated-fields.ts    # Auto-generated base field configs
├── fieldOverrides.ts      # UI-specific customizations
├── createNodeConfig.ts    # Helper to create node configs
├── index.ts              # Exports all node configs
├── nodeMeta.ts           # Node metadata (icons, colors, labels)
├── helpers.ts            # Utility functions
└── [node-type].ts        # Individual node configurations
```