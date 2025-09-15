"""Example usage patterns for the enhanced service registry with safety rails."""

from __future__ import annotations

from typing import Any

from dipeo.config import get_settings

from .enhanced_service_registry import (
    EnhancedServiceKey,
    EnhancedServiceRegistry,
    ServiceType,
    core_service,
    domain_service,
    final_service,
    immutable_service,
    test_registry_context,
)


def example_basic_usage():
    """Example: Basic service registration and resolution."""
    print("=== Basic Usage Example ===")

    # Create registry
    registry = EnhancedServiceRegistry()

    # Create service keys with metadata
    db_key = EnhancedServiceKey[Any](
        name="database",
        service_type=ServiceType.ADAPTER,
        description="Main database connection",
        dependencies=("config_service",),
    )

    config_key = EnhancedServiceKey[Any](
        name="config_service", service_type=ServiceType.CORE, description="Configuration service"
    )

    # Register services
    class ConfigService:
        def get(self, key: str) -> str:
            return f"config_value_for_{key}"

    class DatabaseService:
        def __init__(self, config: ConfigService):
            self.config = config
            self.connection_string = config.get("db_url")

        def query(self, sql: str) -> list[dict]:
            return [{"result": f"data_for_{sql}"}]

    # Register config first (dependency)
    registry.register(config_key, ConfigService())

    # Register database with factory function
    def create_database():
        config = registry.resolve(config_key)
        return DatabaseService(config)

    registry.register(db_key, create_database)

    # Resolve and use services
    config_service = registry.resolve(config_key)
    print(f"Config value: {config_service.get('example')}")

    db_service = registry.resolve(db_key)
    print(f"Query result: {db_service.query('SELECT * FROM users')}")

    # Validate dependencies
    missing_deps = registry.validate_dependencies()
    print(f"Missing dependencies: {missing_deps}")


def example_safety_rails():
    """Example: Safety rails and protection mechanisms."""
    print("\n=== Safety Rails Example ===")

    registry = EnhancedServiceRegistry()

    # Create protected services
    core_db_key = final_service(
        "core_database",
        service_type=ServiceType.CORE,
        description="Core database service that cannot be overridden",
    )

    cache_key = immutable_service(
        "cache_service",
        service_type=ServiceType.ADAPTER,
        description="Cache service that becomes immutable after first registration",
    )

    # Register protected services
    class CoreDatabase:
        def __init__(self):
            self.connections = {"main": "connected"}

    class CacheService:
        def __init__(self):
            self.cache = {}

    registry.register(core_db_key, CoreDatabase())
    registry.register(cache_key, CacheService())

    print("Protected services registered successfully")

    # Try to override final service (should fail)
    try:
        registry.register(core_db_key, CoreDatabase(), override=True)
        print("ERROR: Final service override should have failed!")
    except RuntimeError as e:
        print(f"✓ Final service protection working: {e}")

    # Try to override immutable service (should fail)
    try:
        registry.register(cache_key, CacheService(), override=True)
        print("ERROR: Immutable service override should have failed!")
    except RuntimeError as e:
        print(f"✓ Immutable service protection working: {e}")

    # Freeze registry
    registry.freeze()
    print("Registry frozen")

    # Try to register new service after freeze (should fail)
    try:
        new_key = EnhancedServiceKey[Any]("new_service")
        registry.register(new_key, "new_service")
        print("ERROR: Registration after freeze should have failed!")
    except RuntimeError as e:
        print(f"✓ Freeze protection working: {e}")


def example_audit_trail():
    """Example: Audit trail and monitoring."""
    print("\n=== Audit Trail Example ===")

    registry = EnhancedServiceRegistry(enable_audit=True)

    # Register some services with overrides
    service_key = EnhancedServiceKey[Any](
        "example_service", description="Service for audit demonstration"
    )

    # Initial registration
    registry.register(service_key, "initial_value")

    # Override with reason
    registry.register(
        service_key, "updated_value", override=True, override_reason="Configuration update required"
    )

    # Get audit trail
    audit_trail = registry.get_audit_trail("example_service")
    print(f"Audit records for example_service: {len(audit_trail)}")

    for record in audit_trail:
        print(f"  {record.timestamp}: {record.action} - {record.success}")
        if record.override_reason:
            print(f"    Reason: {record.override_reason}")
        if record.error_message:
            print(f"    Error: {record.error_message}")

    # Get comprehensive service info
    service_info = registry.get_service_info("example_service")
    print(f"\nService info: {service_info}")


def example_testing_utilities():
    """Example: Testing utilities and patterns."""
    print("\n=== Testing Utilities Example ===")

    # Use test registry context for isolated testing
    with test_registry_context() as test_registry:
        print("Created isolated test registry")

        # Register test services
        test_key = EnhancedServiceKey[Any]("test_service")
        test_registry.register(test_key, "test_value")

        # Use temporary overrides
        with test_registry.temporary_override({test_key: "temporary_value"}):
            value = test_registry.resolve(test_key)
            print(f"Temporary value: {value}")

        # Original value restored
        original_value = test_registry.resolve(test_key)
        print(f"Restored value: {original_value}")

    print("Test registry context exited - cleanup automatic")


def example_child_registries():
    """Example: Child registries for scoped services."""
    print("\n=== Child Registries Example ===")

    # Parent registry with shared services
    parent_registry = EnhancedServiceRegistry()

    shared_config_key = core_service("shared_config", description="Shared configuration service")

    class SharedConfig:
        def __init__(self):
            self.settings = {"env": "production", "debug": False}

    parent_registry.register(shared_config_key, SharedConfig())

    # Child registry for specific scope
    child_registry = parent_registry.create_child(scoped_service="child_specific_value")

    # Child can access parent services
    shared_config = child_registry.resolve(shared_config_key)
    print(f"Shared config from child: {shared_config.settings}")

    # Child has its own services
    scoped_key = EnhancedServiceKey[Any]("scoped_service")
    scoped_value = child_registry.resolve(scoped_key)
    print(f"Scoped service: {scoped_value}")

    # Parent doesn't have child services
    try:
        parent_registry.resolve(scoped_key)
        print("ERROR: Parent should not have child service!")
    except KeyError:
        print("✓ Child services properly isolated from parent")


def example_production_patterns():
    """Example: Production-ready patterns and best practices."""
    print("\n=== Production Patterns Example ===")

    # Production registry with strict settings
    registry = EnhancedServiceRegistry(
        allow_override=False,  # Strict override policy
        enable_audit=True,  # Full audit trail
    )
    registry._environment = "production"

    # Define core services as final
    database_key = final_service(
        "production_database",
        service_type=ServiceType.CORE,
        description="Production database connection pool",
        dependencies=("connection_config", "monitoring_service"),
    )

    config_key = final_service(
        "connection_config",
        service_type=ServiceType.CORE,
        description="Database connection configuration",
    )

    monitoring_key = core_service(
        "monitoring_service", description="Application monitoring and metrics"
    )

    # Register core services
    class ConnectionConfig:
        def __init__(self):
            self.connection_string = "postgresql://prod:5432/app"
            self.pool_size = 20

    class MonitoringService:
        def __init__(self):
            self.metrics = {}

        def record_metric(self, name: str, value: float):
            self.metrics[name] = value

    class ProductionDatabase:
        def __init__(self, config: ConnectionConfig, monitoring: MonitoringService):
            self.config = config
            self.monitoring = monitoring
            self.pool = f"pool({config.pool_size})"

        def execute(self, query: str):
            self.monitoring.record_metric("db_query", 1.0)
            return f"executed: {query}"

    # Register with dependency injection
    registry.register(config_key, ConnectionConfig())
    registry.register(monitoring_key, MonitoringService())

    def create_database():
        config = registry.resolve(config_key)
        monitoring = registry.resolve(monitoring_key)
        return ProductionDatabase(config, monitoring)

    registry.register(database_key, create_database)

    # Freeze after bootstrap
    registry.freeze()
    print("Production registry bootstrapped and frozen")

    # Validate all dependencies are satisfied
    missing_deps = registry.validate_dependencies()
    if missing_deps:
        print(f"⚠️  Missing dependencies: {missing_deps}")
    else:
        print("✓ All dependencies satisfied")

    # Use services
    db = registry.resolve(database_key)
    result = db.execute("SELECT * FROM users")
    print(f"Database query result: {result}")

    # Try invalid override in production (should fail)
    try:
        registry.register(
            database_key,
            "malicious_override",
            override=True,
            override_reason="Attempted security breach",
        )
    except RuntimeError as e:
        print(f"✓ Production override protection: {e}")


def example_configuration_integration():
    """Example: Integration with DiPeO configuration system."""
    print("\n=== Configuration Integration Example ===")

    # Get settings from DiPeO config
    settings = get_settings()

    # Create registry with settings-based configuration
    registry = EnhancedServiceRegistry(
        allow_override=settings.dependency_injection.allow_override,
        enable_audit=settings.dependency_injection.enable_audit,
    )

    print("Registry configured from settings:")
    print(f"  Environment: {settings.env}")
    print(f"  Allow override: {settings.dependency_injection.allow_override}")
    print(f"  Enable audit: {settings.dependency_injection.enable_audit}")
    print(f"  Freeze after boot: {settings.dependency_injection.freeze_after_boot}")

    # Use configuration-driven service registration
    if settings.dependency_injection.validate_dependencies_on_boot:
        print("Dependency validation enabled")

    if settings.dependency_injection.freeze_after_boot and settings.env == "production":
        print("Auto-freeze enabled for production")


def run_all_examples():
    """Run all usage examples."""
    print("DiPeO Enhanced Service Registry - Usage Examples")
    print("=" * 50)

    try:
        example_basic_usage()
        example_safety_rails()
        example_audit_trail()
        example_testing_utilities()
        example_child_registries()
        example_production_patterns()
        example_configuration_integration()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
