# DiPeO Code Generation & GraphQL Schema Architecture

## Overview

DiPeO uses a sophisticated code generation pipeline with TypeScript domain models as the single source of truth. The system generates Python models, GraphQL schemas, and TypeScript types to ensure type consistency across the entire stack.

## Architecture Flow

```
┌─────────────────────────┐
│  TypeScript Domain      │  ← Single Source of Truth
│  (domain-models/src/)   │    - diagram.ts, execution.ts, conversation.ts
└───────────┬─────────────┘
            │
            ▼ npm run build
┌─────────────────────────┐
│  Schema Extraction      │  ← ts-morph analyzes TypeScript AST
│  (generate-schema.ts)   │    → outputs schemas.json
└───────────┬─────────────┘
            │
      ┌─────┴─────┬─────────────┬──────────────┐
      ▼           ▼             ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Python   │ │ GraphQL  │ │   CLI    │ │TypeScript│
│ Models   │ │  Schema  │ │  Models  │ │  Types   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
     │            │             │            │
     ▼            ▼             ▼            ▼
dipeo-domain   Server API    CLI Tool    Web App
     │
     ▼
┌──────────────────────────────────────────────────────┐
│             Python Package Ecosystem                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │dipeo-core│ │ dipeo-   │ │  dipeo-  │ │ dipeo- │ │
│  │          │ │ diagram  │ │ usecases │ │services│ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└──────────────────────────────────────────────────────┘
```

## Generation Pipeline

### 1. TypeScript → JSON Schema
**Script**: `generate-schema.ts`
- Uses ts-morph to parse TypeScript AST
- Extracts interfaces, enums, and their properties
- Outputs `__generated__/schemas.json`

### 2. JSON Schema → Python Models
**Script**: `generate-python.ts`
- Reads schemas.json
- Generates Pydantic models with:
  - Proper type mappings (TS → Python)
  - Snake_case field names with aliases
  - Optional fields handling
  - Branded types as NewType

**Output**: `packages/python/dipeo_domain/src/dipeo_domain/models.py`

#### Python Package Architecture
The generated models form the foundation for multiple Python packages:
- **dipeo-domain**: Generated Pydantic models for server (direct output)
- **dipeo-core**: Base abstractions and protocols
- **dipeo-diagram**: Diagram conversion utilities
- **dipeo-application**: Application layer handlers and DTOs (shared between server and CLI)
- **dipeo-infra**: Infrastructure layer implementations
- **dipeo-container**: Dependency injection container

Note: The CLI uses lightweight dataclasses instead of Pydantic models to avoid server dependencies.

### 3. TypeScript → GraphQL Schema
**Script**: `generate-graphql.ts`
- Direct TypeScript to GraphQL SDL conversion
- Maps TypeScript types to GraphQL types
- Handles enums, unions, and custom scalars

**Output**: `packages/domain-models/schema.graphql`

### 4. Server → GraphQL Schema Export
The FastAPI server uses Strawberry GraphQL to:
- Define queries, mutations, and subscriptions
- Export complete schema including operations
- Use Pydantic models for type safety

**Output**: `apps/server/schema.graphql`

### 5. GraphQL Schema → TypeScript Types
**Tool**: GraphQL Code Generator (`codegen.yml`)
- Reads server's GraphQL schema
- Generates TypeScript types and React hooks
- Maps custom scalars to branded types from domain-models

**Output**: `apps/web/src/__generated__/graphql.tsx`

### 6. CLI Code Generation (Implemented)
The CLI uses a different approach than the server, with two custom generation scripts:

#### TypeScript → CLI Models
**Script**: `generate-cli.ts`
- Reads TypeScript domain models
- Generates lightweight Python dataclasses (not Pydantic)
- Optimized for CLI usage without server dependencies

**Output**: `apps/cli/src/dipeo_cli/__generated__/models.py`

#### GraphQL Operations → Python
**Script**: `apps/cli/scripts/generate_graphql_operations.py`
- Parses GraphQL operation files (.graphql)
- Generates typed Python operations
- Creates operation strings and variable types

**Output**: `apps/cli/src/dipeo_cli/__generated__/graphql_operations.py`

**Note**: While `apps/cli/codegen.yml` exists, it references a non-existent "python" plugin and is not currently used.

### 7. Application Layer DTOs (New)
**Script**: `generate-dto.ts`
- Reads TypeScript domain models
- Generates Python dataclass DTOs for the application layer
- Provides data transfer objects for API boundaries

**Output**: `packages/python/dipeo_application/src/dipeo_application/dto/__generated__.py`

## Key Components

### Branded Types
TypeScript branded types ensure type safety:
```typescript
export type NodeID = string & { readonly __brand: 'NodeID' };
```

Mapped in Python as:
```python
NodeID = NewType('NodeID', str)
```

### Type Mappings

| TypeScript  | Python     | GraphQL |
|-------------|------------|---------|
| string      | str        | String  |
| number      | float/int  | Float   |
| boolean     | bool       | Boolean |
| T[]         | List[T]    | [T]     |
| Record<K,V> | Dict[K,V]  | JSON    |
| enum        | Enum       | enum    |

### Field Name Conversion
- TypeScript: `camelCase`
- Python: `snake_case` (with Pydantic aliases)
- GraphQL: `camelCase`

## Build Process

1. **Initial Setup**: `./build-all.sh`
   - Builds domain models
   - Installs Python packages
   - Generates GraphQL schema
   - Runs frontend codegen

2. **Quick Commands**:
   ```bash
   # Full code generation (recommended after domain model changes)
   make codegen
   
   # Export GraphQL schema from server
   make graphql-schema
   
   # Start all development servers
   make dev-all
   ```

3. **Development Workflow**:
   ```bash
   # After changing domain models:
   cd packages/domain-models
   pnpm build  # Regenerates all derived code
   
   # Or use the Makefile:
   make codegen  # Runs all generation steps
   
   # The generation includes:
   # 1. TypeScript → JSON Schema
   # 2. JSON Schema → Python Pydantic models
   # 3. TypeScript → GraphQL SDL
   # 4. TypeScript → CLI dataclass models
   # 5. TypeScript → Application DTOs
   # 6. Server → GraphQL schema export
   # 7. GraphQL → Frontend types
   # 8. GraphQL operations → CLI Python code
   ```

4. **Installing Python Packages**:
   ```bash
   # Install all dependencies
   make install
   
   # Or manually:
   pip install -e packages/python/dipeo_domain
   pip install -e packages/python/dipeo_core
   pip install -e packages/python/dipeo_diagram
   pip install -e packages/python/dipeo_application
   pip install -e packages/python/dipeo_infra
   pip install -e packages/python/dipeo_container
   ```

5. **Pre-commit Hooks**:
   ```bash
   # Install pre-commit
   pip install pre-commit
   
   # Install git hooks
   pre-commit install
   
   # Domain model changes will automatically trigger regeneration on commit
   ```

## GraphQL Architecture

### Schema Organization
- **Types**: Auto-generated from domain models
- **Queries**: Defined in `queries.py`
- **Mutations**: Modular (per domain) in `mutations/`
- **Subscriptions**: Real-time updates in `subscriptions.py`

### Strawberry Integration
```python
@strawberry.experimental.pydantic.type(DomainNode, all_fields=True)
class DomainNodeType:
    # Automatic conversion from Pydantic models
    pass
```

### Custom Scalars
Defined in both schema and codegen config:
- NodeID, DiagramID, ExecutionID, etc.
- DateTime, JSONScalar

## Benefits

1. **Type Safety**: End-to-end type checking from database to UI
2. **Single Source of Truth**: All types derive from TypeScript models
3. **Consistency**: Field names, enums, and types stay synchronized
4. **Developer Experience**: Auto-completion and type checking everywhere
5. **Maintainability**: Change types in one place, regenerate everywhere
6. **Code Reuse**: Shared packages enable both server and CLI to use same logic
7. **Local Execution**: CLI can run diagrams without server dependency

## Common Tasks

### Adding a New Field
1. Add to TypeScript interface in `domain-models/src/`
2. Run `pnpm build` in domain-models
3. Restart server to load new Python models
4. Run `pnpm codegen` in web app

### Adding a New Type
1. Create interface/enum in domain-models
2. Follow same regeneration process
3. Add GraphQL operations as needed
4. Update codegen if using new scalars

### Debugging Generation
- Check `__generated__/schemas.json` for extraction issues
- Python models have clear imports at top
- GraphQL schema is human-readable
- Use `--verbose` flags in generation scripts

## Complete Generation Pipeline

The full code generation flow when running `make codegen`:

1. **Domain Models Build** (`packages/domain-models/`):
   - TypeScript compilation
   - Schema extraction to JSON
   - Python Pydantic models generation
   - GraphQL SDL generation
   - CLI dataclass models generation
   - Application DTOs generation

2. **GraphQL Schema Export** (`apps/server/`):
   - Server exports complete schema with operations
   - Includes queries, mutations, subscriptions

3. **Frontend Codegen** (`apps/web/`):
   - Reads server GraphQL schema
   - Generates TypeScript types and hooks

4. **CLI Operations** (`apps/cli/`):
   - Generates Python GraphQL operation code

## Troubleshooting

### Common Issues

1. **"Schema file not found" error**:
   - Run `pnpm generate:schema` first
   - Ensure you're in the correct directory

2. **Python import errors after generation**:
   - Reinstall packages: `pip install -e packages/python/dipeo_domain`
   - Check Python path configuration

3. **TypeScript types not updating**:
   - Clear build cache: `rm -rf packages/domain-models/dist`
   - Rebuild: `pnpm build`

4. **GraphQL schema mismatch**:
   - Ensure server is running when exporting schema
   - Run `make graphql-schema` to update

### Validation Steps

1. **After domain model changes**:
   ```bash
   # Verify all generations completed
   ls packages/python/dipeo_domain/src/dipeo_domain/models.py
   ls packages/domain-models/schema.graphql
   ls apps/cli/src/dipeo_cli/__generated__/models.py
   ```

2. **Check for type consistency**:
   - Compare enum values between TS and Python
   - Verify field names match (with case conversion)
   - Ensure all interfaces are generated

3. **Test the pipeline**:
   ```bash
   # Run a simple diagram to test end-to-end
   ./dipeo run files/diagrams/native/quicksave.json --debug
   ```