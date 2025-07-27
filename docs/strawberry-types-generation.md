# Strawberry GraphQL Types Generation

This document describes the automated generation of Strawberry GraphQL types from the domain schema in DiPeO.

## Overview

DiPeO now automatically generates Strawberry GraphQL types from the `domain-schema.graphql` file, eliminating the need for manual type definitions in the server. This reduces boilerplate code by ~70% and ensures type consistency across the stack.

## Architecture

### Generation Flow

1. **TypeScript Models** → **domain-schema.graphql** (via domain model generation)
2. **domain-schema.graphql** → **Strawberry Types** (via new generator)

### Key Components

- **Generator**: `files/codegen/code/backend/generators/strawberry_types.py`
- **DiPeO Diagram**: `files/codegen/diagrams/backend/generate_strawberry_types.light.yaml`
- **Output**: `apps/server/src/dipeo_server/api/graphql/__generated__/types.py`

## Benefits

1. **Reduced Boilerplate**: ~300+ lines of manual type definitions eliminated
2. **Type Safety**: Automatic synchronization with domain models
3. **Documentation**: Rich GraphQL descriptions preserved from schema
4. **Maintainability**: Changes to TypeScript models automatically propagate

## Usage

### Generate Strawberry Types

The Strawberry types are generated as part of the backend batch generation:

```bash
# Generate all backend files (includes Strawberry types)
dipeo run codegen/diagrams/backend/generate_backend_batch_ts --light --debug --no-browser

# Or generate everything
make codegen
```

### Using Generated Types

Import types from the generated module:

```python
from dipeo_server.api.graphql.__generated__.types import (
    # Scalars
    NodeID, ArrowID, HandleID, PersonID, ApiKeyID, DiagramID, ExecutionID, JSONScalar,
    
    # Enums (with Enum suffix)
    NodeTypeEnum, HandleDirectionEnum, ExecutionStatusEnum,
    
    # Types (with Type suffix)
    DomainNodeType, DomainArrowType, DomainDiagramType,
    StartNodeDataType, PersonJobNodeDataType,
    
    # Special cases (no Type suffix)
    BaseNodeData, TypescriptAstNodeData,
    
    # Input types
    ExecutionUpdate,
    
    # Unions
    NodeData
)
```

## Implementation Details

### Type Mapping

The generator handles several type mappings:

1. **Scalars**: Custom scalar types with serialization/parsing
2. **Enums**: Converted to `strawberry.enum()`
3. **Pydantic Types**: Wrapped with `@strawberry.experimental.pydantic.type`
4. **Regular Types**: Defined as `@strawberry.type`
5. **Input Types**: Defined as `@strawberry.input`

### Special Cases

1. **DBNodeData**: Maps from GraphQL `DBNodeData` to Python `DbNodeData`
2. **BaseNodeData**: Regular Strawberry type (not Pydantic)
3. **TypescriptAstNodeData**: Regular Strawberry type (not Pydantic)

### Import Structure

The generated file imports:
- Domain models from `dipeo.diagram_generated.domain_models`
- Node data types from `dipeo.diagram_generated.models.*`
- Enums from `dipeo.diagram_generated.enums`

## Migration Guide

### From Manual Types to Generated

1. **Backup existing types**: `cp types.py types.py.backup`
2. **Generate new types**: `make codegen`
3. **Update imports**: Change from manual types to generated
4. **Test thoroughly**: Ensure all GraphQL operations work

### Transitional Approach

A transitional `types_new.py` is provided that:
- Imports all generated types
- Adds server-specific input/result types
- Maintains backward compatibility

## Future Improvements

1. **Schema Validation**: Use domain-schema.graphql for validation
2. **Documentation Portal**: Serve schema as API documentation
3. **Testing Infrastructure**: Generate mock data from schema
4. **Federation Support**: Use as base schema for microservices

## Troubleshooting

### Common Issues

1. **Import errors**: Check case sensitivity (DbNodeData vs DBNodeData)
2. **Missing types**: Ensure all node models are in manifests
3. **Syntax errors**: Re-run generation after fixing parser

### Debugging

```bash
# Test generated types
cd apps/server
python test_generated_types.py

# Check generated file
cat src/dipeo_server/api/graphql/__generated__/types.py
```

## Summary

The Strawberry type generation system demonstrates DiPeO's self-hosting capabilities - using its own visual programming system to generate its own code. This approach ensures type safety, reduces manual work, and maintains consistency across the entire stack.