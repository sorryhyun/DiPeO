# DiPeO Model Generation Scripts

This directory contains all code generation scripts for the DiPeO models package. Scripts are organized by their target platform and purpose.

## Directory Structure

```
scripts/
├── frontend/       # Frontend-specific generation scripts
├── backend/        # Backend-specific generation scripts  
├── shared/         # Shared/foundation scripts used by both
└── README.md       # This file
```

## Frontend Scripts (`frontend/`)

Scripts that generate code specifically for the React/TypeScript frontend:

- **generate-frontend-mappings.ts** - Generates GraphQL to domain type mappings for Apollo Client
- **generate-react-hooks.ts** - Generates React hooks for GraphQL operations
- **generate-zod-schemas.ts** - Generates Zod validation schemas for runtime type checking

## Backend Scripts (`backend/`)

Scripts that generate code specifically for the Python/FastAPI backend:

- **generate-python.ts** - Generates Python/Pydantic models from TypeScript interfaces
- **generate-graphql-resolvers.ts** - Generates Python GraphQL resolver functions
- **integrate-generated-entities.py** - Python script to integrate generated entities into the backend

## Shared Scripts (`shared/`)

Foundation scripts that generate code or schemas used by both frontend and backend:

- **generate-entities.ts** - Generates entity definitions from configuration
- **generate-entity-interfaces.ts** - Generates TypeScript interfaces (source of truth)
- **generate-graphql-types.ts** - Generates GraphQL type definitions
- **generate-schema.ts** - Core schema generation from TypeScript AST
- **generate-conversions.ts** - Generates type conversion utilities
- **generate-field-configs.ts** - Generates field configuration mappings
- **generate-static-nodes.ts** - Generates static node type definitions
- **load-schema.ts** - Utility for loading generated schemas

## Usage

Scripts are typically run through npm/pnpm scripts defined in `package.json`:

```bash
# Generate all code
pnpm generate:all

# Generate specific targets
pnpm generate:python      # Backend Python models
pnpm generate:frontend    # Frontend mappings and hooks
pnpm generate:graphql     # GraphQL types and resolvers
```

## Adding New Scripts

When adding new generation scripts:

1. Place in the appropriate subdirectory based on target:
   - `frontend/` for React/TypeScript-specific output
   - `backend/` for Python/FastAPI-specific output
   - `shared/` for schemas or code used by both

2. Update this README with the script's purpose

3. Add corresponding npm script in `package.json` if needed

## Script Execution Order

Some scripts depend on others. The typical generation flow is:

1. **shared/generate-schema.ts** - Extracts TypeScript AST
2. **shared/generate-entities.ts** - Creates entity definitions
3. **shared/generate-graphql-types.ts** - Creates GraphQL schemas
4. Platform-specific scripts can then run in parallel:
   - **backend/generate-python.ts** - Python models
   - **frontend/generate-frontend-mappings.ts** - TypeScript mappings
   - etc.