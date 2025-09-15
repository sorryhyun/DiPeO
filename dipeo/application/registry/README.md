# Enhanced Service Registry with Safety Rails

This document provides comprehensive documentation for DiPeO's enhanced service registry system, which implements robust dependency injection with comprehensive safety rails, audit trails, and production-ready controls.

## Overview

The Enhanced Service Registry addresses the safety rails problem described in advice.md #1 by providing:

- **Environment-based controls** with automatic behavior based on dev/test/prod
- **Comprehensive audit trail** for all registrations and override attempts
- **Decorator pattern** for marking services as immutable/final
- **Context managers** for safe testing with temporary overrides
- **Partial freezing** capability for granular control
- **Enhanced error messages** with context and suggestions
- **Type safety** with improved validation

## Key Components

### 1. EnhancedServiceKey

```python
@dataclass(frozen=True, slots=True)
class EnhancedServiceKey[T]:
    name: str
    final: bool = False                    # Cannot be overridden even in dev/test
    immutable: bool = False               # Cannot be overridden after first registration
    service_type: ServiceType = ServiceType.APPLICATION
    description: str = ""                 # Human-readable description
    dependencies: tuple[str, ...] = ()    # Service dependencies
```

**Service Types:**
- `CORE`: Core infrastructure services
- `DOMAIN`: Domain services
- `APPLICATION`: Application services
- `ADAPTER`: Infrastructure adapters
- `REPOSITORY`: Data repositories
- `FACTORY`: Service factories

### 2. EnhancedServiceRegistry

The main registry class with comprehensive safety features:

```python
class EnhancedServiceRegistry:
    def __init__(self, *, allow_override: bool | None = None, enable_audit: bool = True)
    def register(self, key: EnhancedServiceKey[T], service: T | Callable[[], T],
                *, override: bool = False, override_reason: str | None = None)
    def resolve(self, key: EnhancedServiceKey[T]) -> T
    def freeze(self, services: list[str] | None = None)
    def temporary_override(self, overrides: dict[EnhancedServiceKey[Any], Any])
    # ... many more methods
```

### 3. Configuration Integration

```python
class DependencyInjectionSettings(BaseSettings):
    # Override Control
    allow_override: bool = False

    # Freezing Behavior
    freeze_after_boot: bool = True
    auto_freeze_in_production: bool = True

    # Audit Trail
    enable_audit: bool = True
    audit_max_records: int = 1000

    # Safety Features
    require_override_reason_in_prod: bool = True
    validate_dependencies_on_boot: bool = True
```

## Safety Rails

### 1. Environment-Based Controls

The registry automatically adjusts behavior based on environment:

**Development/Testing:**
- Overrides allowed by default
- Temporary overrides permitted
- Lenient final service constraints

**Production:**
- Strict override controls
- Override reasons required
- Automatic freezing after bootstrap
- Enhanced audit logging

### 2. Service Protection Levels

**Final Services:**
```python
# Cannot be overridden even in dev/test (except testing environment)
db_key = final_service("core_database",
                      service_type=ServiceType.CORE,
                      description="Core database connection")
```

**Immutable Services:**
```python
# Cannot be overridden after first registration
cache_key = immutable_service("cache_service",
                             service_type=ServiceType.ADAPTER)
```

**Frozen Services:**
```python
# Freeze specific services or entire registry
registry.freeze(["critical_service", "security_service"])
registry.freeze()  # Freeze entire registry
```

### 3. Constraint Validation

The registry validates multiple constraints before allowing registration:

1. **Registry freeze state** - Blocks registration if frozen
2. **Service freeze state** - Blocks registration of individually frozen services
3. **Final constraints** - Prevents override of final services
4. **Immutable constraints** - Prevents override after first registration
5. **Override policy** - Enforces environment-based override rules
6. **Production requirements** - Requires override reasons in production

## Audit Trail

### Registration Records

Every action is recorded with comprehensive context:

```python
@dataclass(frozen=True)
class RegistrationRecord:
    timestamp: datetime
    service_key: str
    action: str  # 'register', 'override', 'freeze', 'unregister'
    caller_info: str  # file:line where registration happened
    environment: str
    success: bool
    error_message: str | None = None
    override_reason: str | None = None
```

### Audit Trail Access

```python
# Get audit trail for specific service
trail = registry.get_audit_trail("my_service")

# Get full audit trail
full_trail = registry.get_audit_trail()

# Analyze failed registrations
failed_attempts = [r for r in trail if not r.success]
```

## Testing Utilities

### 1. RegistryTestCase

Base test case with comprehensive testing utilities:

```python
class MyServiceTest(RegistryTestCase):
    def test_service_registration(self):
        key = self.register_test_service("my_service", final=True)
        self.assert_service_registered(key)
        self.assert_service_resolvable(key)

        # Test protection
        self.assert_override_fails(key, "new_value")

        # Check audit trail
        self.assert_audit_trail_contains("my_service", "register")
```

### 2. Test Context Managers

```python
# Isolated test registry
with test_registry_context() as test_registry:
    # Test in isolation
    pass

# Temporary overrides for testing
with registry.temporary_override({service_key: mock_service}):
    # Test with mock service
    pass
```

### 3. Mock Factories

```python
# Create various types of mock services
simple_service = MockServiceFactory.create_simple_service()
failing_factory = MockServiceFactory.create_failing_factory()
stateful_service = MockServiceFactory.create_stateful_service({"count": 0})
```

## Usage Patterns

### 1. Basic Registration

```python
# Create registry
registry = EnhancedServiceRegistry()

# Define service keys
config_key = EnhancedServiceKey[ConfigService](
    name="config_service",
    service_type=ServiceType.CORE,
    description="Application configuration"
)

# Register services
registry.register(config_key, ConfigService())

# Resolve services
config = registry.resolve(config_key)
```

### 2. Factory Registration

```python
# Register factory function
def create_database():
    config = registry.resolve(config_key)
    return DatabaseService(config)

registry.register(database_key, create_database)
```

### 3. Protected Services

```python
# Core infrastructure that must not be overridden
core_db_key = final_service("core_database",
                           service_type=ServiceType.CORE)

# Services that become immutable after registration
cache_key = immutable_service("cache_service")

registry.register(core_db_key, CoreDatabase())
registry.register(cache_key, CacheService())
```

### 4. Child Registries

```python
# Create child for scoped services
child_registry = parent_registry.create_child(
    scoped_service="child_value"
)

# Child inherits parent services but can override locally
child_registry.register(local_key, LocalService())
```

### 5. Production Bootstrap

```python
# Production-ready bootstrap pattern
def bootstrap_production_services(registry: EnhancedServiceRegistry):
    # Register core services as final
    registry.register(final_service("database"), create_database)
    registry.register(final_service("cache"), create_cache)
    registry.register(core_service("monitoring"), MonitoringService())

    # Validate dependencies
    missing_deps = registry.validate_dependencies()
    if missing_deps:
        raise RuntimeError(f"Missing dependencies: {missing_deps}")

    # Freeze after bootstrap
    registry.freeze()

    return registry
```

## Error Messages and Debugging

### Enhanced Error Messages

The registry provides detailed error messages with context:

```
Service not found: user_service
Similar services: user_repository, user_validator, user_cache
Available services: 23 registered
```

### Service Information

```python
info = registry.get_service_info("my_service")
# Returns:
{
    "name": "my_service",
    "type": "instance",  # or "factory"
    "service_type": "application",
    "description": "User management service",
    "final": False,
    "immutable": True,
    "frozen": False,
    "resolve_count": 42,
    "dependencies": ["user_repository", "email_service"],
    "class": "UserService"
}
```

## Configuration

### Environment Variables

```bash
# Override Control
DIPEO_DI_ALLOW_OVERRIDE=false

# Freezing Behavior
DIPEO_DI_FREEZE_AFTER_BOOT=true
DIPEO_DI_AUTO_FREEZE_PRODUCTION=true

# Audit Trail
DIPEO_DI_ENABLE_AUDIT=true
DIPEO_DI_AUDIT_MAX_RECORDS=1000

# Safety Features
DIPEO_DI_REQUIRE_OVERRIDE_REASON_PROD=true
DIPEO_DI_VALIDATE_DEPENDENCIES=true

# Development Features
DIPEO_DI_ALLOW_TEMP_OVERRIDES=true
DIPEO_DI_STRICT_FINAL_SERVICES=true
```

### Programmatic Configuration

```python
from dipeo.config import get_settings

settings = get_settings()
registry = EnhancedServiceRegistry(
    allow_override=settings.dependency_injection.allow_override,
    enable_audit=settings.dependency_injection.enable_audit
)
```

## Migration Guide

### From Original ServiceRegistry

**Before:**
```python
registry = ServiceRegistry()
registry.register(ServiceKey("my_service"), MyService())
```

**After:**
```python
registry = EnhancedServiceRegistry()
key = EnhancedServiceKey[MyService](
    name="my_service",
    service_type=ServiceType.APPLICATION,
    description="My application service"
)
registry.register(key, MyService())
```

### Backward Compatibility

The enhanced registry maintains backward compatibility:

```python
# These aliases maintain compatibility
ServiceKey = EnhancedServiceKey
ServiceRegistry = EnhancedServiceRegistry
```

## Best Practices

### 1. Service Key Design

- Use descriptive names and descriptions
- Specify appropriate service types
- Mark critical services as final
- Document dependencies clearly

### 2. Registration Patterns

- Register dependencies before dependents
- Use factory functions for complex construction
- Provide override reasons in production
- Validate dependencies after bootstrap

### 3. Testing

- Use `RegistryTestCase` for comprehensive test utilities
- Leverage temporary overrides for isolated testing
- Test both success and failure scenarios
- Verify audit trail for security-sensitive operations

### 4. Production Deployment

- Use strict configuration in production
- Freeze registry after bootstrap
- Monitor audit trail for security issues
- Validate all dependencies are satisfied

### 5. Error Handling

- Catch and handle `KeyError` for missing services
- Check service existence with `has()` before resolution
- Use `get()` with defaults for optional services
- Monitor resolution failures in audit trail

## Security Considerations

### 1. Override Protection

- Final services cannot be overridden (except in testing)
- Production overrides require explicit reasons
- All override attempts are audited
- Temporary overrides restricted to non-production

### 2. Audit Trail

- All registration actions are logged with caller context
- Failed attempts are recorded with error details
- Audit trail is bounded to prevent memory issues
- Production deployments should monitor for suspicious activity

### 3. Dependency Validation

- Missing dependencies are detected at bootstrap
- Circular dependencies can be identified
- Service hierarchy can be validated
- Security-critical services can be marked as final

## Troubleshooting

### Common Issues

**"Registry is frozen" Error:**
- Check if registry was frozen after bootstrap
- Use `override=True` if override is intentional
- Verify environment allows overrides

**"Cannot override final service" Error:**
- Final services cannot be overridden in production
- Check if service was marked as `final=True`
- Use testing environment for test overrides

**"Service not found" Error:**
- Check service name spelling
- Verify service was registered
- Use `list_services()` to see available services

**Missing Dependencies:**
- Use `validate_dependencies()` to find missing deps
- Register dependencies before dependents
- Check service key names match exactly

### Debugging Tools

```python
# List all services
services = registry.list_services()

# Find unused services
unused = registry.report_unused()

# Check service information
info = registry.get_service_info("service_name")

# Validate dependencies
missing = registry.validate_dependencies()

# Review audit trail
trail = registry.get_audit_trail()
```

## Performance Considerations

- Service resolution is O(1) for instances
- Factory services are cached after first resolution
- Audit trail is bounded to prevent memory growth
- Thread-safe operations use RLock for minimal contention
- Child registries inherit efficiently without copying services

This enhanced service registry provides production-ready dependency injection with comprehensive safety rails while maintaining the flexibility needed for development and testing workflows.
