# DiPeO Service Registry

This package provides a type-safe service registry for the DiPeO application layer, consolidating the previous scattered registry implementations.

## Overview

The new registry system provides:
- **Type Safety**: ServiceKey pattern ensures compile-time type checking
- **Thread Safety**: All operations are thread-safe with proper locking
- **Hierarchical Support**: Child registries can inherit from parents
- **Migration Path**: Adapter for gradual migration from old registry

## Key Components

### ServiceKey
Type-safe keys for service lookup:
```python
from dipeo.application.registry import ServiceKey, LLM_SERVICE

# Define a key with type
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")

# Use with full type safety
llm = registry.resolve(LLM_SERVICE)  # Type: LLMServicePort
```

### ServiceRegistry
Thread-safe registry implementation:
```python
from dipeo.application.registry import ServiceRegistry

registry = ServiceRegistry()
registry.register(LLM_SERVICE, llm_instance)
service = registry.resolve(LLM_SERVICE)
```

### MigrationServiceRegistry
Backward-compatible adapter for gradual migration:
```python
from dipeo.application.registry.migration_adapter import MigrationServiceRegistry

# Supports both old and new patterns
registry = MigrationServiceRegistry()
old_way = registry.get("llm_service")  # String-based
new_way = registry.resolve(LLM_SERVICE)  # ServiceKey-based
```

## Migration Guide

### Phase 1 (Current)
- ✅ New registry structure created
- ✅ ServiceKeys defined for all services
- ✅ Containers updated to use MigrationServiceRegistry
- ✅ Deprecation warnings added to old registries
- ✅ Migration examples provided

### Phase 2 (Next Steps)
- Update all handlers to use ServiceKey pattern
- Migrate GraphQL resolvers
- Remove string-based lookups
- Delete deprecated registries

## Usage Examples

See `migration_examples.py` for detailed examples of:
- Converting string-based lookups to ServiceKey pattern
- Updating handlers and resolvers
- Defining custom service keys
- Using the migration adapter

## Benefits

1. **Type Safety**: IDE autocomplete and compile-time checking
2. **Maintainability**: Single source of truth for services
3. **Architecture**: Proper separation - registry only in application layer
4. **Performance**: Pre-resolved services with caching
5. **Debugging**: Clear service dependencies and lifecycle