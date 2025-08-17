# Diagram Services V2 Migration Guide

## Overview

This guide explains how to migrate from the old diagram services in `dipeo/infrastructure/services/diagram/` to the new adapter-based implementation in `dipeo/infrastructure/adapters/diagram/`.

## Current State

### Old Implementation (To Be Replaced)
- **Location**: `dipeo/infrastructure/services/diagram/`
  - `CompilationService` - Infrastructure wrapper for diagram compilation
  - `ConverterService` - Format conversion service  
  - `DiagramService` - Main orchestrator for diagram operations

### New Implementation (Already Available)
- **Location**: `dipeo/infrastructure/adapters/diagram/`
  - `compiler_adapter.py` - Compilation adapters with caching and validation
  - `serializer_adapter.py` - Serialization/conversion adapters
  - `resolution_adapter.py` - Input resolution adapters

### Wiring System (Ready to Use)
- **Location**: `dipeo/application/wiring/diagram_wiring.py`
- Feature flag support for gradual migration
- Environment variable configuration

## Migration Steps

### Step 1: Enable V2 Services via Environment Variables

Add these environment variables to your `.env` file or export them:

```bash
# Enable V2 for all diagram services
export DIAGRAM_PORT_V2=1

# Or enable specific services individually
export DIAGRAM_COMPILER_V2=1
export DIAGRAM_SERIALIZER_V2=1  
export DIAGRAM_RESOLUTION_V2=1

# Optional configuration
export DIAGRAM_USE_INTERFACE_COMPILER=1  # Use interface-based compiler (recommended)
export DIAGRAM_COMPILER_CACHE=1          # Enable compilation caching
export DIAGRAM_COMPILER_VALIDATE=1       # Enable validation
export DIAGRAM_COMPILER_CACHE_SIZE=100   # Cache size
export DIAGRAM_SERIALIZER_CACHE=1        # Enable serializer caching
```

### Step 2: Update Application Bootstrap

Replace direct service instantiation with wiring:

**OLD** (in `dipeo/application/bootstrap/application_container.py`):
```python
from dipeo.infrastructure.services.diagram import DiagramConverterService, CompilationService

# Direct instantiation
self.registry.register(
    DIAGRAM_CONVERTER,
    DiagramConverterService()
)

self.registry.register(
    COMPILATION_SERVICE,
    CompilationService()
)
```

**NEW**:
```python
from dipeo.application.wiring.diagram_wiring import wire_all_diagram_services

# Use wiring system
wire_all_diagram_services(self.registry)
```

### Step 3: Update Service Resolution

Update code that resolves diagram services to use the new registry tokens:

**OLD**:
```python
from dipeo.application.registry.keys import DIAGRAM_SERVICE, COMPILATION_SERVICE

diagram_service = registry.resolve(DIAGRAM_SERVICE)
compilation_service = registry.resolve(COMPILATION_SERVICE)
```

**NEW**:
```python
from dipeo.application.registry.registry_tokens import (
    DIAGRAM_PORT,
    DIAGRAM_COMPILER,
    DIAGRAM_SERIALIZER
)

diagram_port = registry.resolve(DIAGRAM_PORT)
compiler = registry.resolve(DIAGRAM_COMPILER)
serializer = registry.resolve(DIAGRAM_SERIALIZER)
```

### Step 4: Update GraphQL and CLI Usage

Update mutations and commands to use the new service interfaces:

**Example GraphQL Mutation Update**:
```python
# OLD
from dipeo.infrastructure.services.diagram import DiagramConverterService
converter = DiagramConverterService()
await converter.initialize()
domain_diagram = converter.deserialize_from_storage(content, format_hint)

# NEW  
serializer = registry.resolve(DIAGRAM_SERIALIZER)
domain_diagram = serializer.deserialize_from_storage(content, format_hint)
```

## Benefits of V2 Architecture

### 1. **Separation of Concerns**
- Compilation logic separated from serialization
- Clear adapter boundaries
- Infrastructure concerns isolated from domain logic

### 2. **Performance Optimizations**
- Optional caching for compilation and serialization
- LRU cache eviction for memory efficiency
- Configurable cache sizes

### 3. **Validation**
- Optional validation adapter wrapper
- Early error detection before compilation
- Better error messages

### 4. **Flexibility**
- Choose between different compiler implementations
- Strategy pattern for format handling
- Easy to add new format support

### 5. **Gradual Migration**
- Feature flags allow rollback
- Can enable per-service or all at once
- No breaking changes to API

## Testing the Migration

### 1. Verify Services Are Wired
```python
# Check that services are registered
assert registry.resolve(DIAGRAM_COMPILER) is not None
assert registry.resolve(DIAGRAM_SERIALIZER) is not None
```

### 2. Test Compilation
```python
compiler = registry.resolve(DIAGRAM_COMPILER)
executable = compiler.compile(domain_diagram)
assert executable is not None
```

### 3. Test Serialization
```python
serializer = registry.resolve(DIAGRAM_SERIALIZER)
content = serializer.serialize_for_storage(diagram, "light")
restored = serializer.deserialize_from_storage(content, "light")
assert restored.id == diagram.id
```

## Rollback Plan

If issues arise, disable V2 by setting environment variables:

```bash
export DIAGRAM_PORT_V2=0
# Or unset the variables
unset DIAGRAM_PORT_V2
unset DIAGRAM_COMPILER_V2
unset DIAGRAM_SERIALIZER_V2
```

## Cleanup After Migration

Once V2 is stable and tested:

1. Remove old service files:
   - `dipeo/infrastructure/services/diagram/compilation_service.py`
   - `dipeo/infrastructure/services/diagram/converter_service.py`
   - `dipeo/infrastructure/services/diagram/diagram_service.py` (after creating V2 replacement)

2. Remove V1 code paths from wiring:
   - Update `diagram_wiring.py` to remove V1 branches
   - Set V2 as default

3. Update imports throughout codebase to use new tokens

## Implementation Status

- ✅ Compiler adapters implemented
- ✅ Serializer adapters implemented  
- ✅ Resolution adapters implemented
- ✅ Wiring system with feature flags
- ⚠️ Need to create UnifiedDiagramService for DIAGRAM_PORT
- ⚠️ Need to update application bootstrap
- ⚠️ Need to update GraphQL mutations
- ⚠️ Need to update CLI commands

## Next Steps

1. Create `UnifiedDiagramService` that uses the new adapters
2. Update `application_container.py` to use wiring
3. Test with feature flags enabled
4. Update all service resolution points
5. Remove old services after successful migration