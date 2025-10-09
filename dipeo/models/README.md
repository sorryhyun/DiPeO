# DiPeO Models - TypeScript Specifications

This directory contains the **source of truth** for DiPeO's node types, GraphQL operations, and code generation system. All TypeScript specifications here drive code generation for the backend Python code and frontend React components.

## Overview

The DiPeO models system uses **TypeScript as the modeling language** for defining:
- **Node Specifications**: Complete definitions of diagram node types
- **GraphQL Operations**: Query, mutation, and subscription definitions
- **Code Generation Mappings**: TypeScript → Python type mappings
- **Frontend Types**: React component interfaces and Zod schemas

All generated code in `/dipeo/diagram_generated/` is produced from these TypeScript specifications. **Never edit generated code directly** - always modify the specs here and regenerate.

## Directory Structure

```
dipeo/models/
├── src/
│   ├── nodes/              # Node type specifications (17 specs)
│   │   ├── person-job.spec.ts
│   │   ├── api-job.spec.ts
│   │   ├── code-job.spec.ts
│   │   └── ...
│   ├── frontend/           # GraphQL query definitions
│   │   ├── query-definitions/
│   │   ├── query-builder.ts
│   │   ├── query-enums.ts
│   │   └── query-specifications.ts
│   ├── codegen/            # Code generation configurations
│   │   ├── mappings.ts     # Type mappings (TS → Python, Zod, etc.)
│   │   ├── node-interface-map.ts
│   │   └── ast-types.ts
│   ├── core/               # Core domain types
│   │   ├── diagram.ts
│   │   ├── execution.ts
│   │   ├── conversation.ts
│   │   ├── enums/
│   │   └── types/
│   ├── utilities/          # Helper functions
│   ├── node-specification.ts  # Type definitions for specs
│   ├── node-categories.ts     # Node categorization
│   └── index.ts               # Public exports
├── dist/                   # Compiled JavaScript output
├── package.json
└── tsconfig.json
```

## Node Specification Anatomy

A complete `NodeSpecification` defines everything needed to generate a working node type:

### Complete Example (person-job.spec.ts)

```typescript
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const personJobSpec: NodeSpecification = {
  // === Basic Metadata ===
  nodeType: NodeType.PERSON_JOB,
  displayName: "Person Job",
  category: "ai",
  icon: "🤖",
  color: "#2196F3",
  description: "Execute tasks using AI language models",

  // === Field Definitions ===
  fields: [
    {
      name: "person",
      type: "string",
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
      validation: {
        minLength: 1,
        maxLength: 50000
      },
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
      name: "max_iteration",
      type: "number",
      required: true,
      defaultValue: 100,
      description: "Maximum execution iterations",
      validation: {
        min: 1,
        max: 1000
      },
      uiConfig: {
        inputType: "number",
        min: 1
      }
    }
  ],

  // === Handle Configuration ===
  handles: {
    inputs: ["default", "first"],
    outputs: ["default"]
  },

  // === Input Ports (SEAC) ===
  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data for prompt template"
    },
    {
      name: "first",
      contentType: "object",
      required: false,
      description: "Input for first iteration only"
    }
  ],

  // === Output Specification ===
  outputs: {
    result: {
      type: "any",
      description: "AI response and results"
    }
  },

  // === Execution Configuration ===
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  // === UI Configuration ===
  primaryDisplayField: "person",

  // === Handler Metadata (Code Generation) ===
  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.person_job",
    className: "PersonJobHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["LLM_CLIENT", "STATE_STORE", "EVENT_BUS"],
    skipGeneration: true  // Already has custom handler
  },

  // === Examples ===
  examples: [
    {
      name: "Basic AI Task",
      description: "Simple AI task with prompt",
      configuration: {
        person: "default",
        default_prompt: "Summarize the input text",
        max_iteration: 1
      }
    },
    {
      name: "Iterative Analysis",
      description: "Multi-iteration analysis with memory",
      configuration: {
        person: "analyst",
        default_prompt: "Analyze the data and provide insights",
        max_iteration: 5,
        memorize_to: "requirements,acceptance criteria"
      }
    }
  ]
};
```

## Specification Components

### 1. Basic Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nodeType` | `NodeType` | Yes | Unique identifier (enum) |
| `displayName` | `string` | Yes | Human-readable name |
| `category` | `NodeCategory` | Yes | Category: "ai", "integration", "logic", etc. |
| `icon` | `string` | Yes | Emoji or icon identifier |
| `color` | `string` | Yes | Hex color for UI |
| `description` | `string` | Yes | Brief description |

### 2. Field Specifications

Each field defines a configurable property of the node:

```typescript
{
  name: string;              // Field identifier (snake_case recommended)
  type: FieldType;           // "string" | "number" | "boolean" | "object" | "enum"
  required: boolean;         // Is field required?
  description: string;       // Help text
  defaultValue?: any;        // Default value
  validation?: ValidationRules;  // Validation constraints
  uiConfig: UIConfiguration;     // UI rendering config
  nestedFields?: FieldSpecification[];  // For object types
  affects?: string[];        // Fields affected by this field
  conditional?: ConditionalConfig;  // Show/hide based on other fields
}
```

**Field Types:**
- `"string"` - Text fields
- `"number"` - Numeric fields
- `"boolean"` - Checkboxes
- `"enum"` - Dropdown selections (use `allowedValues`)
- `"object"` - Nested JSON objects
- `"array"` - Lists of items

**UI Input Types:**
- `"text"` - Single-line text input
- `"textarea"` - Multi-line text
- `"number"` - Number input with min/max
- `"checkbox"` - Boolean toggle
- `"select"` - Dropdown with options
- `"code"` - Code editor with syntax highlighting
- `"personSelect"` - Person picker
- Custom types as needed

### 3. Validation Rules

```typescript
validation: {
  min?: number;           // Minimum value (numbers)
  max?: number;           // Maximum value (numbers)
  minLength?: number;     // Minimum length (strings)
  maxLength?: number;     // Maximum length (strings)
  pattern?: string;       // Regex pattern
  message?: string;       // Custom error message
  allowedValues?: string[];  // Enum values
  itemType?: FieldType;   // For arrays
}
```

### 4. Handle Configuration

Defines connection points for diagram arrows:

```typescript
handles: {
  inputs: string[];   // Input handle IDs (e.g., ["default", "first"])
  outputs: string[];  // Output handle IDs (e.g., ["default", "success", "error"])
}
```

### 5. Input Ports (SEAC)

**SEAC (Strict Envelopes & Arrow Contracts)** enforces type-safe connections:

```typescript
inputPorts: [
  {
    name?: string;      // Port name (optional for single port)
    contentType: 'raw_text' | 'object' | 'conversation_state' | 'binary';
    required: boolean;  // Must be connected?
    default?: any;      // Default if not connected
    accepts?: string[]; // Type hints for validation
    description?: string;
  }
]
```

**When to define inputPorts:**
- ✅ **Always define** for proper type checking
- ✅ Prevents runtime type mismatches
- ✅ Enables compile-time arrow validation
- ⚠️ Currently only 12% of specs have inputPorts (target: 100%)

### 6. Output Specification

```typescript
outputs: {
  result: {
    type: DataType | 'any';  // Output data type
    description: string;     // What the output contains
  }
}
```

### 7. Execution Configuration

```typescript
execution: {
  timeout?: number;        // Default timeout in seconds
  retryable?: boolean;     // Can retry on failure?
  maxRetries?: number;     // Max retry attempts
  requires?: string[];     // Dependencies (e.g., ["numpy", "pandas"])
}
```

### 8. Handler Metadata

**Critical for code generation** - defines the backend handler:

```typescript
handlerMetadata: {
  modulePath?: string;     // Python module path
  className?: string;      // Handler class name
  mixins?: string[];       // Mixins to include
  serviceKeys?: string[];  // Required services from ServiceRegistry
  skipGeneration?: boolean;  // Skip codegen (for custom handlers)
  customImports?: string[];  // Additional imports
}
```

**Common Service Keys:**
- `LLM_CLIENT` - AI language model client
- `STATE_STORE` - State management
- `EVENT_BUS` - Event system
- `HTTP_CLIENT` - HTTP requests
- `DB_CLIENT` - Database access

**Common Mixins:**
- `LoggingMixin` - Logging utilities
- `ValidationMixin` - Input validation
- `ConfigurationMixin` - Configuration management

### 9. Examples

Provide 2+ examples for documentation and testing:

```typescript
examples: [
  {
    name: string;               // Example name
    description: string;        // What it demonstrates
    configuration: Record<string, any>;  // Field values
  }
]
```

## Code Generation Workflow

The complete code generation workflow:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. TypeScript Specs (Source of Truth)                       │
│    /dipeo/models/src/                                       │
│    - nodes/*.spec.ts                                        │
│    - frontend/query-definitions/*.ts                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Build TypeScript                                          │
│    $ cd dipeo/models && pnpm build                          │
│    Output: dipeo/models/dist/*.js                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. IR (Intermediate Representation) Builders                 │
│    Python scripts read compiled JS and build IR             │
│    $ make codegen                                           │
│    - Read node specs from dist/                             │
│    - Apply type mappings (TS → Python)                      │
│    - Generate Python dataclasses, handlers, GraphQL         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Generated Code (Staged)                                  │
│    /dipeo/diagram_generated_staged/                         │
│    - models/            # Pydantic models                   │
│    - operations.py      # GraphQL operations                │
│    - handlers/          # Node handler stubs                │
│    - __generated__/     # Frontend types                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Review & Apply                                           │
│    $ make diff-staged    # Review changes                   │
│    $ make apply-test     # Apply with validation            │
│    Moves staged → /dipeo/diagram_generated/                 │
└─────────────────────────────────────────────────────────────┘
```

### Quick Commands

```bash
# Full codegen workflow
cd dipeo/models && pnpm build  # Compile TypeScript
make codegen                    # Generate code → staged/
make diff-staged                # Review changes
make apply-test                 # Apply with tests

# Update GraphQL schema
make graphql-schema             # Regenerate schema

# Type checking
cd dipeo/models && pnpm typecheck
```

## Type Mappings

### TypeScript → Python

Defined in `src/codegen/mappings.ts`:

| TypeScript | Python | Notes |
|------------|--------|-------|
| `string` | `str` | |
| `number` | `int` | |
| `boolean` | `bool` | |
| `any` | `JsonValue` | Union type |
| `Record<string, any>` | `JsonDict` | Dict[str, Any] |
| `string[]` | `Optional[List[str]]` | |
| `PersonID` | `Optional[PersonID]` | Branded type |

### Branded Types

Use branded types for type safety:

```typescript
// In core/enums/
export enum NodeType {
  PERSON_JOB = "person_job",
  API_JOB = "api_job"
}

// Usage in spec
nodeType: NodeType.PERSON_JOB  // ✅ Type-safe
nodeType: "person_job"         // ❌ Avoid string literals
```

**Available Branded Types:**
- `PersonID`, `NodeID`, `HandleID`, `ArrowID`
- `NodeType`, `SupportedLanguage`, `HttpMethod`
- `DBBlockSubType`, `HookType`, `ContentType`

## Adding a New Node Type

### Step-by-Step Guide

**1. Create Node Specification**

Create `src/nodes/my-node.spec.ts`:

```typescript
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const myNodeSpec: NodeSpecification = {
  nodeType: NodeType.MY_NODE,
  displayName: "My Node",
  category: "integration",
  icon: "⚡",
  color: "#FF5722",
  description: "Does something awesome",

  fields: [
    {
      name: "config_value",
      type: "string",
      required: true,
      description: "Configuration value",
      uiConfig: {
        inputType: "text",
        placeholder: "Enter value..."
      }
    }
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },

  inputPorts: [
    {
      contentType: "object",
      required: false,
      description: "Input data"
    }
  ],

  outputs: {
    result: {
      type: "any",
      description: "Output result"
    }
  },

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.my_node",
    className: "MyNodeHandler",
    mixins: ["LoggingMixin", "ValidationMixin"],
    serviceKeys: ["STATE_STORE"]
  },

  examples: [
    {
      name: "Basic Example",
      description: "Simple usage",
      configuration: {
        config_value: "example"
      }
    }
  ]
};
```

**2. Add to NodeType Enum**

Update `src/core/enums/node-types.ts`:

```typescript
export enum NodeType {
  // ... existing types
  MY_NODE = "my_node"
}
```

**3. Register in Index**

Add to `src/nodes/index.ts`:

```typescript
export { myNodeSpec } from './my-node.spec.js';
```

**4. Build & Generate**

```bash
cd dipeo/models
pnpm build
cd ../..
make codegen
make diff-staged
make apply-test
```

**5. Implement Handler**

Generated stub at `/dipeo/application/execution/handlers/my_node.py`:

```python
from dipeo.domain.handlers import BaseNodeHandler
from dipeo.application.mixins import LoggingMixin, ValidationMixin

class MyNodeHandler(LoggingMixin, ValidationMixin, BaseNodeHandler):
    async def execute(self, input_data):
        # Implement handler logic
        config_value = self.config.config_value
        # ... your implementation
        return {"result": "output"}
```

**6. Update GraphQL Schema**

```bash
make graphql-schema
```

**7. Test**

```bash
dipeo run examples/my_test_diagram --light --debug
```

## Best Practices

### ✅ DO

- **Define inputPorts** for all nodes (SEAC type safety)
- **Add handlerMetadata** for code generation
- **Provide 2+ examples** for documentation
- **Use branded types** (enums) instead of string literals
- **Use snake_case** for field names (Python convention)
- **Add descriptions** to all fields and outputs
- **Specify validation rules** for inputs
- **Use defaultValue** for optional fields
- **Add JSDoc comments** for better IDE support
- **Test generated code** before committing

### ❌ DON'T

- Don't edit `/dipeo/diagram_generated/` directly
- Don't skip `inputPorts` definition
- Don't use string literals for enums
- Don't mix camelCase and snake_case
- Don't duplicate validation in `validation` and `uiConfig`
- Don't forget to rebuild TypeScript after changes
- Don't skip examples (aim for 100% coverage)

## Validation

### Spec Validation

Use the built-in validators:

```typescript
import { validateFieldSpecification } from './node-specification.js';

const errors = validateFieldSpecification(field);
if (errors.length > 0) {
  console.error('Validation errors:', errors);
}
```

### Runtime Validation

```bash
# Type checking
cd dipeo/models && pnpm typecheck

# Build (validates imports)
pnpm build
```

## Current Status

### Coverage Metrics

| Metric | Current | Target | Progress |
|--------|---------|--------|----------|
| Handler Metadata | 3/17 (18%) | 17/17 (100%) | 🟥 |
| Examples | 4/17 (24%) | 17/17 (100%) | 🟥 |
| InputPorts | 2/17 (12%) | 17/17 (100%) | 🟥 |
| Strong Enum Typing | 0/17 (0%) | 17/17 (100%) | 🟥 |

### Improvement Roadmap

See [TODO.md](./TODO.md) for the complete 4-week improvement plan covering:
- **Week 1:** Foundation (query validation, architecture docs, enums)
- **Week 2:** Type safety (strong enums, inputPorts, branded types)
- **Week 3:** Consistency (validation patterns, field presets)
- **Week 4:** Quality (documentation, examples, polish)

## Troubleshooting

### TypeScript Build Errors

```bash
cd dipeo/models
pnpm typecheck  # Check for type errors
pnpm build      # Rebuild
```

### Codegen Failures

```bash
# Check logs
cat .logs/cli.log

# Run with debug
make codegen --debug

# Validate specs
cd dipeo/models && pnpm build
```

### GraphQL Schema Issues

```bash
# Regenerate schema
make graphql-schema

# Check frontend types
cd apps/web && pnpm typecheck
```

## Related Documentation

- [Code Generation Guide](../../docs/projects/code-generation-guide.md)
- [Overall Architecture](../../docs/architecture/overall_architecture.md)
- [GraphQL Layer](../../docs/architecture/graphql-layer.md)
- [Node Handler Development](../../docs/architecture/node-handlers.md)

## Contributing

When adding or modifying specifications:

1. Follow the patterns in existing specs
2. Add complete metadata (handlerMetadata, inputPorts, examples)
3. Use strong typing (enums, branded types)
4. Add validation rules
5. Test generated code
6. Update documentation
7. Run type checking and builds

## Questions?

- Check existing specs in `src/nodes/` for patterns
- Review type definitions in `node-specification.ts`
- See mappings in `src/codegen/mappings.ts`
- Consult architecture docs in `/docs/`

---

**Last Updated:** 2025-10-09
**Specs Version:** 0.1.0
**Total Node Types:** 17
