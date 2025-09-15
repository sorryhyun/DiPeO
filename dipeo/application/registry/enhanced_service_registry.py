"""Enhanced type-safe service registry for DiPeO application layer with comprehensive safety rails."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar, cast

T = TypeVar("T")


class ServiceType(Enum):
    """Service registration types for better categorization."""

    CORE = "core"  # Core infrastructure services
    DOMAIN = "domain"  # Domain services
    APPLICATION = "application"  # Application services
    ADAPTER = "adapter"  # Infrastructure adapters
    REPOSITORY = "repository"  # Data repositories
    FACTORY = "factory"  # Service factories


@dataclass(frozen=True)
class RegistrationRecord:
    """Audit record for service registrations and override attempts."""

    timestamp: datetime
    service_key: str
    action: str  # 'register', 'override', 'freeze', 'unregister'
    caller_info: str  # file:line where registration happened
    environment: str
    success: bool
    error_message: str | None = None
    override_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EnhancedServiceKey[T]:
    """Type-safe service key with compile-time type guarantees and enhanced metadata."""

    name: str
    final: bool = False  # Cannot be overridden even in dev/test
    immutable: bool = False  # Cannot be overridden after first registration
    service_type: ServiceType = ServiceType.APPLICATION
    description: str = ""  # Human-readable description
    dependencies: tuple[str, ...] = field(default_factory=tuple)  # Service dependencies

    def __class_getitem__(cls, item):
        """Enable EnhancedServiceKey[ServiceType] syntax for type hints only."""
        return cls

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        qualifiers = []
        if self.final:
            qualifiers.append("final")
        if self.immutable:
            qualifiers.append("immutable")
        qualifier_str = f" ({', '.join(qualifiers)})" if qualifiers else ""
        return f"EnhancedServiceKey[{self.name}]{qualifier_str}"


class EnhancedServiceRegistry:
    """Thread-safe service registry with enhanced safety rails and audit capabilities."""

    def __init__(self, *, allow_override: bool | None = None, enable_audit: bool = True) -> None:
        from dipeo.config import get_settings

        # Core storage
        self._services: dict[str, object] = {}
        self._factories: dict[str, Callable[[], object]] = {}
        self._service_keys: dict[str, EnhancedServiceKey] = {}  # Store original keys with metadata

        # Thread safety
        self._lock = threading.RLock()

        # Metrics and auditing
        self._resolve_hits: dict[str, int] = {}
        self._audit_trail: list[RegistrationRecord] = []
        self._enable_audit = enable_audit

        # Safety rails
        self._frozen = False
        self._frozen_services: set[str] = set()  # Partially frozen services
        self._immutable_services: set[str] = (
            set()
        )  # Services that cannot be overridden after first registration

        # Configuration
        settings = get_settings()
        env = settings.env.lower()
        di_settings = settings.dependency_injection

        # Determine override policy
        if allow_override is not None:
            self._allow_override = allow_override
        else:
            # Allow overrides in dev/test by default, but check settings
            self._allow_override = (
                env in {"development", "dev", "testing", "test"} or di_settings.allow_override
            )

        self._environment = env
        self._freeze_after_boot = di_settings.freeze_after_boot
        self._auto_freeze_in_production = di_settings.auto_freeze_in_production
        self._require_override_reason_in_prod = di_settings.require_override_reason_in_prod
        self._audit_max_records = di_settings.audit_max_records

    def register(
        self,
        key: EnhancedServiceKey[T],
        service: T | Callable[[], T],
        *,
        override: bool = False,
        override_reason: str | None = None,
    ) -> None:
        """Register a service or factory with comprehensive safety checks.

        Args:
            key: Service key with metadata
            service: Service instance or factory function
            override: Explicitly allow override (still subject to other constraints)
            override_reason: Reason for override (for audit trail)

        Raises:
            RuntimeError: If registration violates safety constraints
            ValueError: If invalid parameters provided
        """
        caller_info = self._get_caller_info()

        with self._lock:
            exists = key.name in self._services or key.name in self._factories

            # Check various constraints
            self._check_registration_constraints(
                key, exists, override, override_reason, caller_info
            )

            # Store the key metadata
            self._service_keys[key.name] = key

            # Register the service
            if callable(service) and not hasattr(service, "__self__"):
                self._factories[key.name] = service
                self._services.pop(key.name, None)  # Remove any existing instance
            else:
                self._services[key.name] = service
                self._factories.pop(key.name, None)  # Remove any existing factory

            # Mark as immutable if specified
            if key.immutable:
                self._immutable_services.add(key.name)

            # Record audit trail
            self._record_action(
                key.name,
                "override" if exists else "register",
                caller_info,
                True,
                override_reason=override_reason,
            )

    def resolve(self, key: EnhancedServiceKey[T]) -> T:
        """Resolve a service with type safety and enhanced error reporting."""
        with self._lock:
            if key.name in self._services:
                self._resolve_hits[key.name] = self._resolve_hits.get(key.name, 0) + 1
                return cast(T, self._services[key.name])
            elif key.name in self._factories:
                try:
                    service = self._factories[key.name]()
                    self._services[key.name] = service
                    self._resolve_hits[key.name] = self._resolve_hits.get(key.name, 0) + 1
                    return cast(T, service)
                except Exception as e:
                    caller_info = self._get_caller_info()
                    self._record_action(
                        key.name,
                        "resolve_failed",
                        caller_info,
                        False,
                        error_message=f"Factory failed: {e}",
                    )
                    raise RuntimeError(f"Failed to create service '{key.name}': {e}") from e

            # Enhanced error message with suggestions
            available_services = sorted(self.list_services())
            similar_services = [s for s in available_services if key.name.lower() in s.lower()]

            error_msg = f"Service not found: {key.name}"
            if similar_services:
                error_msg += f"\nSimilar services: {', '.join(similar_services[:3])}"
            if available_services:
                error_msg += f"\nAvailable services: {len(available_services)} registered"

            raise KeyError(error_msg)

    def get(self, key: EnhancedServiceKey[T], default: T | None = None) -> T | None:
        """Get a service with optional default."""
        try:
            return self.resolve(key)
        except KeyError:
            return default

    def has(self, key: EnhancedServiceKey[T]) -> bool:
        """Check if a service is registered."""
        with self._lock:
            return key.name in self._services or key.name in self._factories

    def unregister(self, key: EnhancedServiceKey[T], *, force: bool = False) -> None:
        """Unregister a service with safety checks.

        Args:
            key: Service key to unregister
            force: Force unregistration even for protected services

        Raises:
            RuntimeError: If attempting to unregister protected service without force
        """
        caller_info = self._get_caller_info()

        with self._lock:
            # Check if service exists
            exists = key.name in self._services or key.name in self._factories
            if not exists:
                return

            # Check constraints
            stored_key = self._service_keys.get(key.name)
            if stored_key and not force:
                if stored_key.final:
                    self._record_action(
                        key.name,
                        "unregister_failed",
                        caller_info,
                        False,
                        error_message="Cannot unregister final service without force=True",
                    )
                    raise RuntimeError(
                        f"Cannot unregister final service '{key.name}' without force=True"
                    )

                if key.name in self._frozen_services:
                    self._record_action(
                        key.name,
                        "unregister_failed",
                        caller_info,
                        False,
                        error_message="Cannot unregister frozen service without force=True",
                    )
                    raise RuntimeError(
                        f"Cannot unregister frozen service '{key.name}' without force=True"
                    )

            # Remove the service
            self._services.pop(key.name, None)
            self._factories.pop(key.name, None)
            self._service_keys.pop(key.name, None)
            self._immutable_services.discard(key.name)
            self._frozen_services.discard(key.name)

            # Record audit trail
            self._record_action(key.name, "unregister", caller_info, True)

    def clear(self, *, force: bool = False) -> None:
        """Clear all services with safety checks.

        Args:
            force: Force clearing even protected services

        Raises:
            RuntimeError: If attempting to clear in production without force
        """
        caller_info = self._get_caller_info()

        with self._lock:
            if self._environment == "production" and not force:
                self._record_action(
                    "*",
                    "clear_failed",
                    caller_info,
                    False,
                    error_message="Cannot clear registry in production without force=True",
                )
                raise RuntimeError("Cannot clear registry in production without force=True")

            # Check for final services
            final_services = [
                name for name, key in self._service_keys.items() if key.final and not force
            ]
            if final_services:
                self._record_action(
                    "*",
                    "clear_failed",
                    caller_info,
                    False,
                    error_message=f"Cannot clear final services: {final_services}",
                )
                raise RuntimeError(
                    f"Cannot clear final services without force=True: {final_services}"
                )

            self._services.clear()
            self._factories.clear()
            self._service_keys.clear()
            self._immutable_services.clear()
            self._frozen_services.clear()

            self._record_action("*", "clear", caller_info, True)

    def list_services(self) -> list[str]:
        """List all registered service names."""
        with self._lock:
            return list(set(self._services.keys()) | set(self._factories.keys()))

    def report_unused(self) -> list[str]:
        """Return keys that were registered but never resolved."""
        with self._lock:
            registered = set(self._services) | set(self._factories)
            used = set(k for k, n in self._resolve_hits.items() if n > 0)
            return sorted(registered - used)

    def freeze(self, services: list[str] | None = None) -> None:
        """Freeze the registry or specific services to prevent further modifications.

        Args:
            services: List of service names to freeze. If None, freezes entire registry.
        """
        caller_info = self._get_caller_info()

        with self._lock:
            if services is None:
                self._frozen = True
                action = "freeze_all"
                target = "*"
            else:
                self._frozen_services.update(services)
                action = "freeze_partial"
                target = ", ".join(services)

            self._record_action(target, action, caller_info, True)

    def unfreeze(self, services: list[str] | None = None, *, force: bool = False) -> None:
        """Unfreeze the registry or specific services.

        Args:
            services: List of service names to unfreeze. If None, unfreezes entire registry.
            force: Force unfreezing even in production

        Raises:
            RuntimeError: If attempting to unfreeze in production without force
        """
        caller_info = self._get_caller_info()

        with self._lock:
            if self._environment == "production" and not force:
                self._record_action(
                    "*" if services is None else ", ".join(services),
                    "unfreeze_failed",
                    caller_info,
                    False,
                    error_message="Cannot unfreeze in production without force=True",
                )
                raise RuntimeError("Cannot unfreeze in production without force=True")

            if services is None:
                self._frozen = False
                self._frozen_services.clear()
                action = "unfreeze_all"
                target = "*"
            else:
                for service in services:
                    self._frozen_services.discard(service)
                action = "unfreeze_partial"
                target = ", ".join(services)

            self._record_action(target, action, caller_info, True)

    def is_frozen(self, service: str | None = None) -> bool:
        """Check if registry or specific service is frozen.

        Args:
            service: Service name to check. If None, checks entire registry.

        Returns:
            True if frozen, False otherwise
        """
        with self._lock:
            if service is None:
                return self._frozen
            return self._frozen or service in self._frozen_services

    @contextmanager
    def temporary_override(self, overrides: dict[EnhancedServiceKey[Any], Any]):
        """Context manager for temporary service overrides (testing only).

        Args:
            overrides: Dictionary of service keys to temporary values

        Yields:
            None

        Raises:
            RuntimeError: If used in production environment
        """
        if self._environment == "production":
            raise RuntimeError("Temporary overrides not allowed in production")

        caller_info = self._get_caller_info()
        original_values = {}

        # Store original values and apply overrides
        with self._lock:
            for key, value in overrides.items():
                # Store original if it exists
                if key.name in self._services:
                    original_values[key] = ("service", self._services[key.name])
                elif key.name in self._factories:
                    original_values[key] = ("factory", self._factories[key.name])
                else:
                    original_values[key] = None

                # Apply override
                if callable(value) and not hasattr(value, "__self__"):
                    self._factories[key.name] = value
                    self._services.pop(key.name, None)
                else:
                    self._services[key.name] = value
                    self._factories.pop(key.name, None)

                self._record_action(
                    key.name,
                    "temp_override",
                    caller_info,
                    True,
                    override_reason="Temporary test override",
                )

        try:
            yield
        finally:
            # Restore original values
            with self._lock:
                for key, original in original_values.items():
                    if original is None:
                        # Service didn't exist originally, remove it
                        self._services.pop(key.name, None)
                        self._factories.pop(key.name, None)
                    else:
                        value_type, value = original
                        if value_type == "service":
                            self._services[key.name] = value
                            self._factories.pop(key.name, None)
                        else:
                            self._factories[key.name] = value
                            self._services.pop(key.name, None)

                    self._record_action(
                        key.name,
                        "temp_restore",
                        caller_info,
                        True,
                        override_reason="Restore after temporary override",
                    )

    def override(
        self, key: EnhancedServiceKey[T], service: T | Callable[[], T], *, reason: str = ""
    ) -> None:
        """Explicitly override a service (sugar for register with override=True).

        Args:
            key: Service key to override
            service: New service instance or factory
            reason: Reason for override (for audit trail)
        """
        self.register(key, service, override=True, override_reason=reason)

    def get_audit_trail(self, service: str | None = None) -> list[RegistrationRecord]:
        """Get audit trail for all services or a specific service.

        Args:
            service: Service name to filter by. If None, returns all records.

        Returns:
            List of registration records
        """
        with self._lock:
            if service is None:
                return self._audit_trail.copy()
            return [record for record in self._audit_trail if record.service_key == service]

    def get_service_info(self, service: str) -> dict[str, Any] | None:
        """Get comprehensive information about a service.

        Args:
            service: Service name

        Returns:
            Service information dictionary or None if not found
        """
        with self._lock:
            if service not in self._services and service not in self._factories:
                return None

            key = self._service_keys.get(service)
            service_obj = self._services.get(service) or self._factories.get(service)

            return {
                "name": service,
                "type": "factory" if service in self._factories else "instance",
                "service_type": key.service_type.value if key else "unknown",
                "description": key.description if key else "",
                "final": key.final if key else False,
                "immutable": key.immutable if key else False,
                "frozen": self.is_frozen(service),
                "resolve_count": self._resolve_hits.get(service, 0),
                "dependencies": list(key.dependencies) if key else [],
                "class": service_obj.__class__.__name__ if service_obj else "Unknown",
            }

    def validate_dependencies(self) -> list[str]:
        """Validate that all service dependencies are satisfied.

        Returns:
            List of missing dependencies
        """
        missing = []
        with self._lock:
            for service_name, key in self._service_keys.items():
                for dep in key.dependencies:
                    if not self.has(EnhancedServiceKey[Any](dep)):
                        missing.append(f"{service_name} -> {dep}")
        return missing

    def create_child(self, **services: object) -> ChildServiceRegistry:
        """Create a child registry with inheritance."""
        return ChildServiceRegistry(parent=self, **services)

    def _check_registration_constraints(
        self,
        key: EnhancedServiceKey[T],
        exists: bool,
        override: bool,
        override_reason: str | None,
        caller_info: str,
    ) -> None:
        """Check all registration constraints."""
        # Check if registry is frozen
        if self._frozen and exists and not override:
            self._record_action(
                key.name, "register_failed", caller_info, False, error_message="Registry is frozen"
            )
            raise RuntimeError(f"Registry is frozen; refusing to rebind '{key.name}'")

        # Check if specific service is frozen
        if key.name in self._frozen_services and not override:
            self._record_action(
                key.name, "register_failed", caller_info, False, error_message="Service is frozen"
            )
            raise RuntimeError(f"Service '{key.name}' is frozen; use override=True if necessary")

        # Check final constraint
        stored_key = self._service_keys.get(key.name)
        if stored_key and stored_key.final and self._environment != "testing":
            self._record_action(
                key.name,
                "register_failed",
                caller_info,
                False,
                error_message="Cannot override final service",
            )
            raise RuntimeError(
                f"Cannot override final service '{key.name}' (except in testing environment)"
            )

        # Check immutable constraint
        if key.name in self._immutable_services:
            self._record_action(
                key.name,
                "register_failed",
                caller_info,
                False,
                error_message="Cannot override immutable service",
            )
            raise RuntimeError(f"Cannot override immutable service '{key.name}'")

        # Check general override policy
        if exists and not (override or self._allow_override):
            self._record_action(
                key.name,
                "register_failed",
                caller_info,
                False,
                error_message="Override not allowed without explicit permission",
            )
            raise RuntimeError(
                f"Refusing to overwrite binding for '{key.name}' without override=True "
                f"(env={self._environment}, allow_override={self._allow_override})"
            )

        # Require reason for overrides in production
        if (
            exists
            and override
            and self._environment == "production"
            and self._require_override_reason_in_prod
            and not override_reason
        ):
            self._record_action(
                key.name,
                "register_failed",
                caller_info,
                False,
                error_message="Override reason required in production",
            )
            raise ValueError("Override reason required for production overrides")

    def _record_action(
        self,
        service_key: str,
        action: str,
        caller_info: str,
        success: bool,
        *,
        error_message: str | None = None,
        override_reason: str | None = None,
    ) -> None:
        """Record an action in the audit trail."""
        if not self._enable_audit:
            return

        record = RegistrationRecord(
            timestamp=datetime.now(),
            service_key=service_key,
            action=action,
            caller_info=caller_info,
            environment=self._environment,
            success=success,
            error_message=error_message,
            override_reason=override_reason,
        )

        # Keep audit trail bounded
        if len(self._audit_trail) > self._audit_max_records:
            # Keep last 80% of max records when trimming
            keep_count = int(self._audit_max_records * 0.8)
            self._audit_trail = self._audit_trail[-keep_count:]

        self._audit_trail.append(record)

    @staticmethod
    def _get_caller_info() -> str:
        """Get caller information for audit trail."""
        import inspect

        try:
            # Skip this method and the calling registry method
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                filename = caller_frame.f_code.co_filename
                line_no = caller_frame.f_lineno
                func_name = caller_frame.f_code.co_name

                # Make path relative to project root
                if "/DiPeO/" in filename:
                    filename = filename.split("/DiPeO/", 1)[1]

                return f"{filename}:{line_no} in {func_name}()"
        except (AttributeError, KeyError):
            # Specific exceptions that might occur when inspecting frames
            pass

        return "unknown:0 in unknown()"


class ChildServiceRegistry(EnhancedServiceRegistry):
    """Service registry with parent inheritance and enhanced safety."""

    def __init__(self, parent: EnhancedServiceRegistry, **services: object) -> None:
        # Inherit parent's configuration but allow overrides for testing
        super().__init__(
            allow_override=True,  # Child registries allow overrides by default
            enable_audit=parent._enable_audit,
        )
        self._parent = parent

        # Set environment from parent
        self._environment = parent._environment

        for name, service in services.items():
            key = EnhancedServiceKey[Any](name=name)
            self.register(key, service)

    def resolve(self, key: EnhancedServiceKey[T]) -> T:
        """Resolve a service, checking parent if not found locally."""
        try:
            return super().resolve(key)
        except KeyError:
            return self._parent.resolve(key)

    def has(self, key: EnhancedServiceKey[T]) -> bool:
        """Check if a service is registered in self or parent."""
        return super().has(key) or self._parent.has(key)

    def has_local(self, key: EnhancedServiceKey[T]) -> bool:
        """Check if service exists in local registry only."""
        return super().has(key)

    def get_service_info(self, service: str) -> dict[str, Any] | None:
        """Get service info, checking local first then parent."""
        info = super().get_service_info(service)
        if info is not None:
            info["source"] = "local"
            return info

        parent_info = self._parent.get_service_info(service)
        if parent_info is not None:
            parent_info["source"] = "parent"
        return parent_info


# Decorator functions for creating enhanced service keys
def final_service(name: str, **kwargs) -> EnhancedServiceKey[Any]:
    """Create a final service key that cannot be overridden."""
    return EnhancedServiceKey[Any](name=name, final=True, **kwargs)


def immutable_service(name: str, **kwargs) -> EnhancedServiceKey[Any]:
    """Create an immutable service key that cannot be overridden after first registration."""
    return EnhancedServiceKey[Any](name=name, immutable=True, **kwargs)


def core_service(name: str, **kwargs) -> EnhancedServiceKey[Any]:
    """Create a core infrastructure service key."""
    return EnhancedServiceKey[Any](name=name, service_type=ServiceType.CORE, **kwargs)


def domain_service(name: str, **kwargs) -> EnhancedServiceKey[Any]:
    """Create a domain service key."""
    return EnhancedServiceKey[Any](name=name, service_type=ServiceType.DOMAIN, **kwargs)


# Context manager for test-safe service registration
@contextmanager
def test_registry_context(base_registry: EnhancedServiceRegistry | None = None):
    """Create a test-safe registry context.

    Args:
        base_registry: Base registry to inherit from. If None, creates isolated registry.

    Yields:
        EnhancedServiceRegistry: Test registry instance
    """
    if base_registry is None:
        test_registry = EnhancedServiceRegistry(allow_override=True, enable_audit=True)
        test_registry._environment = "testing"
    else:
        test_registry = base_registry.create_child()

    try:
        yield test_registry
    finally:
        # Cleanup is automatic when context exits
        pass


# Backward compatibility aliases (maintain old ServiceKey interface)
ServiceKey = EnhancedServiceKey
ServiceRegistry = EnhancedServiceRegistry
