"""Test utilities for safe service registry testing."""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from typing import Any, TypeVar
from unittest.mock import Mock

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

T = TypeVar("T")


class RegistryTestCase(unittest.TestCase):
    """Base test case with enhanced registry testing utilities."""

    def setUp(self) -> None:
        """Set up test registry with isolated environment."""
        super().setUp()
        self.registry = EnhancedServiceRegistry(allow_override=True, enable_audit=True)
        self.registry._environment = "testing"

    def tearDown(self) -> None:
        """Clean up test registry."""
        super().tearDown()
        if hasattr(self, "registry"):
            self.registry.clear(force=True)

    def create_test_key(
        self,
        name: str,
        *,
        final: bool = False,
        immutable: bool = False,
        service_type: ServiceType = ServiceType.APPLICATION,
        description: str = "",
        dependencies: tuple[str, ...] = (),
    ) -> EnhancedServiceKey[Any]:
        """Create a test service key with specified attributes."""
        return EnhancedServiceKey[Any](
            name=name,
            final=final,
            immutable=immutable,
            service_type=service_type,
            description=description,
            dependencies=dependencies,
        )

    def register_test_service(
        self,
        name: str,
        service: Any = None,
        *,
        final: bool = False,
        immutable: bool = False,
        service_type: ServiceType = ServiceType.APPLICATION,
    ) -> EnhancedServiceKey[Any]:
        """Register a test service and return its key."""
        if service is None:
            service = Mock(spec_set=[])

        key = self.create_test_key(
            name,
            final=final,
            immutable=immutable,
            service_type=service_type,
            description=f"Test service: {name}",
        )

        self.registry.register(key, service)
        return key

    def assert_service_registered(self, key: EnhancedServiceKey[Any]) -> None:
        """Assert that a service is registered."""
        self.assertTrue(self.registry.has(key), f"Service '{key.name}' should be registered")

    def assert_service_not_registered(self, key: EnhancedServiceKey[Any]) -> None:
        """Assert that a service is not registered."""
        self.assertFalse(self.registry.has(key), f"Service '{key.name}' should not be registered")

    def assert_service_resolvable(self, key: EnhancedServiceKey[Any]) -> Any:
        """Assert that a service can be resolved and return the resolved service."""
        try:
            service = self.registry.resolve(key)
            self.assertIsNotNone(
                service, f"Service '{key.name}' should resolve to a non-None value"
            )
            return service
        except KeyError as e:
            self.fail(f"Service '{key.name}' should be resolvable: {e}")

    def assert_service_frozen(self, service_name: str) -> None:
        """Assert that a service is frozen."""
        self.assertTrue(
            self.registry.is_frozen(service_name), f"Service '{service_name}' should be frozen"
        )

    def assert_registry_frozen(self) -> None:
        """Assert that the entire registry is frozen."""
        self.assertTrue(self.registry.is_frozen(), "Registry should be frozen")

    def assert_audit_trail_contains(
        self, service_name: str, action: str, success: bool = True
    ) -> None:
        """Assert that audit trail contains specific action."""
        trail = self.registry.get_audit_trail(service_name)
        matching_records = [
            record for record in trail if record.action == action and record.success == success
        ]
        self.assertTrue(
            len(matching_records) > 0,
            f"Audit trail should contain {action} action for service '{service_name}'",
        )

    def assert_override_fails(
        self,
        key: EnhancedServiceKey[Any],
        new_service: Any,
        expected_error: type[Exception] = RuntimeError,
    ) -> None:
        """Assert that service override fails with expected error."""
        with self.assertRaises(expected_error):
            self.registry.register(key, new_service, override=True)

    def assert_dependencies_valid(self) -> None:
        """Assert that all service dependencies are satisfied."""
        missing_deps = self.registry.validate_dependencies()
        self.assertEqual(
            [], missing_deps, f"All dependencies should be satisfied. Missing: {missing_deps}"
        )

    @contextmanager
    def assert_no_audit_failures(self):
        """Context manager that asserts no audit failures occurred."""
        initial_trail_length = len(self.registry._audit_trail)
        yield

        new_records = self.registry._audit_trail[initial_trail_length:]
        failed_records = [record for record in new_records if not record.success]

        if failed_records:
            failure_messages = [
                f"{record.action} on {record.service_key}: {record.error_message}"
                for record in failed_records
            ]
            self.fail(f"Audit trail contains failures: {'; '.join(failure_messages)}")


class MockServiceFactory:
    """Factory for creating mock services with various behaviors."""

    @staticmethod
    def create_simple_service(name: str = "test_service") -> Mock:
        """Create a simple mock service."""
        service = Mock(spec_set=[])
        service.name = name
        return service

    @staticmethod
    def create_failing_factory() -> callable:
        """Create a factory that fails during service creation."""

        def failing_factory():
            raise RuntimeError("Factory intentionally failed")

        return failing_factory

    @staticmethod
    def create_dependency_service(dependencies: list[str]) -> Mock:
        """Create a mock service that simulates dependencies."""
        service = Mock(spec_set=["get_dependencies"])
        service.get_dependencies.return_value = dependencies
        return service

    @staticmethod
    def create_stateful_service(initial_state: dict[str, Any] | None = None) -> Mock:
        """Create a mock service with state management."""
        if initial_state is None:
            initial_state = {}

        service = Mock(spec_set=["get_state", "set_state", "reset_state"])
        service._state = initial_state.copy()

        def get_state():
            return service._state.copy()

        def set_state(**kwargs):
            service._state.update(kwargs)

        def reset_state():
            service._state.clear()

        service.get_state.side_effect = get_state
        service.set_state.side_effect = set_state
        service.reset_state.side_effect = reset_state

        return service


class RegistryScenarios:
    """Common test scenarios for registry behavior."""

    @staticmethod
    def test_basic_registration_cycle(test_case: RegistryTestCase) -> None:
        """Test basic service registration, resolution, and unregistration."""
        # Register service
        key = test_case.register_test_service("test_service")
        test_case.assert_service_registered(key)

        # Resolve service
        service = test_case.assert_service_resolvable(key)
        test_case.assertIsNotNone(service)

        # Unregister service
        test_case.registry.unregister(key)
        test_case.assert_service_not_registered(key)

    @staticmethod
    def test_final_service_protection(test_case: RegistryTestCase) -> None:
        """Test final service override protection."""
        # Register final service
        key = test_case.register_test_service("final_service", final=True)
        original_service = test_case.registry.resolve(key)

        # Attempt override should fail
        new_service = MockServiceFactory.create_simple_service("new_service")
        test_case.assert_override_fails(key, new_service)

        # Service should remain unchanged
        current_service = test_case.registry.resolve(key)
        test_case.assertIs(original_service, current_service)

    @staticmethod
    def test_immutable_service_protection(test_case: RegistryTestCase) -> None:
        """Test immutable service override protection."""
        # Register immutable service
        key = test_case.register_test_service("immutable_service", immutable=True)
        original_service = test_case.registry.resolve(key)

        # Attempt override should fail
        new_service = MockServiceFactory.create_simple_service("new_service")
        test_case.assert_override_fails(key, new_service)

        # Service should remain unchanged
        current_service = test_case.registry.resolve(key)
        test_case.assertIs(original_service, current_service)

    @staticmethod
    def test_frozen_registry_protection(test_case: RegistryTestCase) -> None:
        """Test frozen registry override protection."""
        # Register and freeze
        key = test_case.register_test_service("test_service")
        test_case.registry.freeze()
        test_case.assert_registry_frozen()

        # Attempt to register new service should fail
        new_key = test_case.create_test_key("new_service")
        new_service = MockServiceFactory.create_simple_service("new_service")

        with test_case.assertRaises(RuntimeError):
            test_case.registry.register(new_key, new_service)

    @staticmethod
    def test_temporary_override_context(test_case: RegistryTestCase) -> None:
        """Test temporary override context manager."""
        # Register original service
        key = test_case.register_test_service("test_service")
        original_service = test_case.registry.resolve(key)

        # Use temporary override
        temp_service = MockServiceFactory.create_simple_service("temp_service")

        with test_case.registry.temporary_override({key: temp_service}):
            # Should resolve to temporary service
            current_service = test_case.registry.resolve(key)
            test_case.assertIs(temp_service, current_service)

        # Should restore original service
        restored_service = test_case.registry.resolve(key)
        test_case.assertIs(original_service, restored_service)


# Convenience functions for test setup
def create_test_registry(
    *, allow_override: bool = True, enable_audit: bool = True, environment: str = "testing"
) -> EnhancedServiceRegistry:
    """Create a test registry with common test configuration."""
    registry = EnhancedServiceRegistry(allow_override=allow_override, enable_audit=enable_audit)
    registry._environment = environment
    return registry


def register_test_services(
    registry: EnhancedServiceRegistry, service_definitions: dict[str, dict[str, Any]]
) -> dict[str, EnhancedServiceKey[Any]]:
    """Register multiple test services from definitions.

    Args:
        registry: Registry to register services in
        service_definitions: Dict mapping service names to their config

    Returns:
        Dict mapping service names to their keys

    Example:
        keys = register_test_services(registry, {
            "core_service": {
                "service_type": ServiceType.CORE,
                "final": True,
                "dependencies": ["db_service"]
            },
            "db_service": {
                "service_type": ServiceType.ADAPTER
            }
        })
    """
    keys = {}

    for name, config in service_definitions.items():
        service = config.pop("service", MockServiceFactory.create_simple_service(name))

        key = EnhancedServiceKey[Any](
            name=name,
            service_type=config.get("service_type", ServiceType.APPLICATION),
            final=config.get("final", False),
            immutable=config.get("immutable", False),
            description=config.get("description", f"Test service: {name}"),
            dependencies=tuple(config.get("dependencies", [])),
        )

        registry.register(key, service)
        keys[name] = key

    return keys


# Assertion helpers for common test patterns
def assert_service_hierarchy_valid(
    registry: EnhancedServiceRegistry, expected_hierarchy: dict[str, list[str]]
) -> None:
    """Assert that service dependency hierarchy is as expected.

    Args:
        registry: Registry to check
        expected_hierarchy: Dict mapping service names to their expected dependencies
    """
    for service_name, expected_deps in expected_hierarchy.items():
        service_info = registry.get_service_info(service_name)
        if service_info is None:
            raise AssertionError(f"Service '{service_name}' not found in registry")

        actual_deps = service_info["dependencies"]
        if set(actual_deps) != set(expected_deps):
            raise AssertionError(
                f"Service '{service_name}' dependencies mismatch. "
                f"Expected: {expected_deps}, Actual: {actual_deps}"
            )
