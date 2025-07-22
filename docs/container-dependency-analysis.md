# Container System Dependency Analysis

## Overview

After analyzing the DiPeO container system, I've identified several dependency-related issues and areas for improvement. The system uses `dependency-injector` for dependency injection and follows a layered architecture with multiple containers.

## Current Architecture

### Container Hierarchy

1. **Main Container** (`dipeo/container/container.py`)
   - Orchestrates all sub-containers
   - Uses `providers.Container` to wire dependencies
   - Has a circular dependency workaround (line 68)

2. **Sub-Containers**:
   - `BusinessLogicContainer` - Pure business logic (no external deps)
   - `StaticServicesContainer` - Stateless services
   - `PersistenceServicesContainer` - Storage and persistence
   - `IntegrationServicesContainer` - External integrations
   - `DynamicServicesContainer` - Stateful runtime services
   - `ApplicationContainer` - Use cases and orchestration

## Key Issues Found

### 1. Circular Dependency Between Business and Static Containers

**Location**: `container.py` lines 60-68

```python
# Static container (depends on persistence for api_key_service)
static = providers.Container(
    StaticServicesContainer,
    config=config,
    persistence=persistence,
)

# Wire business container's static dependency
business.override_providers(static=static)
```

**Problem**: The business container needs static services, but static is defined after business. This is resolved with a workaround using `override_providers`.

**Impact**: Makes the dependency flow harder to understand and potentially fragile.

### 2. Service Registry Duplication

**Location**: Multiple places create service registries

1. `ApplicationContainer._create_unified_service_registry()` - Creates a registry with all services
2. `ExecutionRuntime` - Has its own `_service_registry`
3. `HandlerFactory` - Sets service registry globally

**Problem**: Multiple sources of truth for service registration, potential for inconsistency.

### 3. Runtime Service Injection

**Location**: `engine.py` lines 140-144

```python
# Register services at runtime
execution_runtime._service_registry.register("diagram", execution_runtime.diagram)
execution_runtime._service_registry.register("execution_context", {
    "interactive_handler": interactive_handler
})
```

**Problem**: Services are registered dynamically during execution, making the dependency graph unclear and harder to test.

### 4. Handler Creation Complexity

**Location**: `handler_factory.py` lines 55-92

The `_create_handler_with_services` method has complex logic for:
- Parameter introspection
- Service name mapping (e.g., `template_service` -> `template`)
- Fallback logic for missing services

**Problem**: Too much "magic" in dependency resolution, making it hard to debug when services are missing.

### 5. Tight Coupling in ExecutionRuntime

**Location**: `execution_runtime.py`

ExecutionRuntime has many responsibilities:
- State management
- Service access
- Input resolution
- Node state transitions
- Execution tracking

**Problem**: Violates Single Responsibility Principle, making testing and maintenance difficult.

## Recommendations

### 1. Resolve Circular Dependencies

Instead of using `override_providers`, consider:
- Creating an interface/protocol that business logic can depend on
- Moving shared services to a separate "common" container
- Using lazy initialization for circular dependencies

### 2. Centralize Service Registration

Create a single source of truth for service registration:
- Define all service keys in one place
- Use the ServiceKey pattern consistently
- Avoid runtime registration where possible

### 3. Simplify Handler Dependency Injection

Make handler dependencies explicit:
- Use constructor injection with clear parameter names
- Avoid parameter name mapping magic
- Consider using a factory pattern with explicit dependencies

### 4. Refactor ExecutionRuntime

Split responsibilities:
- Extract state management to a separate StateManager
- Move service access to a ServiceAccessor
- Keep ExecutionRuntime focused on coordination

### 5. Improve Container Organization

Consider reorganizing containers by:
- **Core**: Domain models and protocols
- **Infrastructure**: External adapters (file, API, DB)
- **Application**: Use cases and orchestration
- **Presentation**: API/CLI specific services

### 6. Add Container Validation

Implement validation to ensure:
- All required services are registered
- No circular dependencies exist
- Service types match expected protocols

## Example Refactoring

Here's how the main container could be reorganized:

```python
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Layer 1: Core (no dependencies)
    core = providers.Container(
        CoreContainer,
        config=config,
    )
    
    # Layer 2: Infrastructure (depends on core)
    infrastructure = providers.Container(
        InfrastructureContainer,
        config=config,
        core=core,
    )
    
    # Layer 3: Domain (depends on core, infrastructure)
    domain = providers.Container(
        DomainContainer,
        config=config,
        core=core,
        infrastructure=infrastructure,
    )
    
    # Layer 4: Application (depends on all lower layers)
    application = providers.Container(
        ApplicationContainer,
        config=config,
        core=core,
        infrastructure=infrastructure,
        domain=domain,
    )
```

This creates a clear dependency hierarchy with no circular dependencies.