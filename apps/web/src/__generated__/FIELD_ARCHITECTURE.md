# Field Configuration Architecture

## Overview

DiPeO uses a layered field configuration system that combines generated and manual configurations:

```
┌─────────────────────────────────────────┐
│         Spec-Based Fields               │ ← Rich UI configs from node specs
│    (__generated__/fields/*Fields.ts)    │   (preferred when available)
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       Domain Model Fields               │ ← Basic fields from TypeScript interfaces
│    (__generated__/nodes/fields.ts)      │   (fallback for nodes without specs)
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Field Overrides                  │ ← Manual UI customizations
│ (features/.../fieldOverrides.ts)        │   (enhancements, not replacements)
└─────────────────────────────────────────┘
```

## Field Sources

### 1. Spec-Based Fields (Primary)
- **Source**: Node specifications (`dipeo/models/src/node-specs/*.spec.ts`)
- **Generated to**: `apps/web/src/__generated__/fields/*Fields.ts`
- **Contains**: Rich field definitions with UI configurations, placeholders, validation
- **Example**: `apiJobFields` in `ApiJobFields.ts`

### 2. Domain Model Fields (Fallback)
- **Source**: TypeScript interfaces (`dipeo/models/src/diagram.ts`)
- **Generated to**: `apps/web/src/__generated__/nodes/fields.ts`
- **Contains**: Basic field definitions derived from data structures
- **Used when**: No spec-based fields exist for a node type

### 3. Field Overrides (Enhancements)
- **Source**: Manual configuration in `fieldOverrides.ts`
- **Purpose**: UI-specific tweaks, custom validation, field ordering
- **Applied to**: Both spec-based and domain model fields

## How They Work Together

### For Generated Node Configs
```typescript
// In __generated__/nodes/ApiJobConfig.ts
import { apiJobFields } from '../fields/ApiJobFields';

export const apiJobConfig: UnifiedNodeConfig = {
  // ... other config
  customFields: apiJobFields,  // Uses spec-based fields directly
};
```

### For Manual Node Configs
```typescript
// Using createNodeConfig
const config = createNodeConfig({
  nodeType: 'my_node',
  // ... other config
});
// This will:
// 1. Try to load spec-based fields
// 2. Fall back to domain model fields
// 3. Apply overrides
```

### Field Resolution Order
```typescript
// In field-utils.ts
async function getBestFieldConfig(nodeType) {
  // 1. Try spec-based fields first (richer)
  if (hasSpecFields(nodeType)) {
    return loadSpecFields(nodeType) + applyOverrides();
  }
  
  // 2. Fall back to domain model fields
  return getDomainFields(nodeType) + applyOverrides();
}
```

## Adding New Fields

### Option 1: Through Node Specification (Recommended)
1. Add field to node spec: `dipeo/models/src/node-specs/my-node.spec.ts`
2. Run: `dipeo run codegen/diagrams/frontend/generate_frontend_single_ts --input-data '{"node_spec_path": "my_node"}'`
3. Fields appear in `__generated__/fields/MyNodeFields.ts`

### Option 2: Through Domain Model
1. Add field to interface: `dipeo/models/src/diagram.ts`
2. Run: `dipeo run codegen/diagrams/models/generate_field_configs`
3. Fields appear in `__generated__/nodes/fields.ts`

### Option 3: Manual Override (UI tweaks only)
1. Add override in `fieldOverrides.ts`
2. This enhances but doesn't replace generated fields

## Best Practices

1. **Prefer spec-based generation** - It produces richer field configs
2. **Use domain models for structural fields** - Basic data that all nodes share
3. **Use overrides for UI polish** - Placeholders, custom validation, ordering
4. **Never edit generated files** - They'll be overwritten
5. **Keep manual code minimal** - Let generation do the heavy lifting

## Common Patterns

### Excluding Generated Fields
```typescript
// In fieldOverrides.ts
NODE_FIELD_OVERRIDES.person_job = {
  excludeFields: ['memory_config'], // Remove deprecated field
};
```

### Adding UI-Only Fields
```typescript
NODE_FIELD_OVERRIDES.person_job = {
  additionalFields: [{
    name: 'memory_profile',
    type: 'select',
    options: [/* ... */]
  }]
};
```

### Reordering Fields
```typescript
NODE_FIELD_OVERRIDES.person_job = {
  fieldOrder: ['label', 'person', 'prompts', 'memory']
};
```