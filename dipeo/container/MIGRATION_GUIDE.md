# Container System Migration Guide

This guide explains the migration from the complex 6-container system to the simplified 3-container architecture.

## Overview

The new container system reduces complexity by consolidating 6 containers into 3:

### Old System (6 containers)
- StaticServicesContainer
- BusinessLogicContainer  
- DynamicServicesContainer
- PersistenceServicesContainer
- IntegrationServicesContainer
- ApplicationContainer

### New System (3 containers)
- **CoreContainer**: Pure domain services (no I/O)
- **InfrastructureContainer**: External adapters (storage, LLM, etc.)
- **ApplicationContainer**: Use cases and orchestration

## Migration Steps

### 1. Enable the New System

Set the environment variable to enable simplified containers:

```bash
export DIPEO_USE_SIMPLE_CONTAINERS=true
```

### 2. Update Container Usage

#### Old Way
```python
from dipeo.container import Container

Container.set_profile('full')  # Complex profiles
container = Container()

# Access through nested containers
llm_service = container.integration.llm_service()
file_service = container.persistence.file_service()
```

#### New Way
```python
from dipeo.container import Container
from dipeo.application.registry.keys import LLM_SERVICE, DIAGRAM_STORAGE

# No profiles needed
container = Container()

# Direct service access
llm_service = container.get_service(LLM_SERVICE)
diagram_storage = container.get_service(DIAGRAM_STORAGE)
```

### 3. Service Key Changes

The new system uses ServiceKey objects for type safety:

```python
# Define service keys
from dipeo.application.registry import ServiceKey

MY_SERVICE = ServiceKey("my_service")

# Register services
container.registry.register(MY_SERVICE, service_instance)

# Resolve services
service = container.registry.resolve(MY_SERVICE)
```

### 4. Configuration Changes

#### Old Way
```python
# Complex configuration with providers
config = providers.Configuration()
config.from_dict(...)
```

#### New Way
```python
from dipeo.core.config import Config

# Simple dataclass configuration
config = Config.from_env()
# or
config = Config(
    storage=StorageConfig(type="local"),
    llm=LLMConfig(provider="openai")
)
```

## Service Mapping

| Old Service Location | New Service Location |
|---------------------|---------------------|
| `container.persistence.file_service()` | `container.get_service(DIAGRAM_STORAGE)` |
| `container.integration.llm_service()` | `container.get_service(LLM_SERVICE)` |
| `container.static.diagram_compiler()` | `container.get_service(COMPILATION_SERVICE)` |
| `container.business.api_validator()` | `container.get_service(DIAGRAM_VALIDATOR)` |
| `container.persistence.api_key_service()` | `container.get_service(API_KEY_SERVICE)` |

## Benefits

1. **Reduced Complexity**: 3 containers instead of 6
2. **Clearer Dependencies**: No circular dependencies between containers
3. **Simpler Configuration**: No complex profiles or provider overrides
4. **Better Type Safety**: ServiceKey pattern provides compile-time guarantees
5. **Easier Testing**: Simple mocking and override patterns

## Gradual Migration

During migration, both systems can coexist:

1. Start with `DIPEO_USE_SIMPLE_CONTAINERS=false` (default)
2. Test individual components with `DIPEO_USE_SIMPLE_CONTAINERS=true`
3. Gradually migrate all usages
4. Remove old container code when complete

## Server Container Migration

For the server application:

```python
# Old way
from dipeo_server.application.container import ServerContainer

# New way (after migration)
from dipeo.container import Container
from dipeo.core.config import Config

# Server-specific configuration
config = Config(
    base_dir=SERVER_BASE_DIR,
    storage=StorageConfig(type="s3", s3_bucket="dipeo-server"),
    llm=LLMConfig(provider="openai", default_model="gpt-4.1-nano")
)

container = Container(config)
```

## Troubleshooting

### Service Not Found
If you get "Service not found" errors:
1. Check if the service key is properly defined
2. Ensure the service is registered in the appropriate container
3. Verify initialization order (Core → Infrastructure → Application)

### Type Errors
The new system is more strict about types:
1. Use ServiceKey objects instead of strings
2. Import service keys from `dipeo.application.registry.keys`
3. Define custom keys using `ServiceKey("name")`

### Configuration Issues
1. Environment variables are loaded automatically with `Config.from_env()`
2. Override specific values by creating a custom Config instance
3. Check `dipeo.core.config` for available configuration options