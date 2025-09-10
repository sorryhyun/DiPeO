"""Type-safe service registry for DiPeO application layer."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, cast

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ServiceKey[T]:
    """Type-safe service key with compile-time type guarantees."""

    name: str

    def __class_getitem__(cls, item):
        """Enable ServiceKey[ServiceType] syntax for type hints only."""
        return cls

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"ServiceKey[{self.name}]"


class ServiceRegistry:
    """Thread-safe service registry with type guarantees."""

    def __init__(self) -> None:
        self._services: dict[str, object] = {}
        self._factories: dict[str, Callable[[], object]] = {}
        self._lock = threading.RLock()
        self._resolve_hits: dict[str, int] = {}

    def register(self, key: ServiceKey[T], service: T | Callable[[], T]) -> None:
        """Register a service or factory."""
        with self._lock:
            if callable(service) and not hasattr(service, "__self__"):
                self._factories[key.name] = service
            else:
                self._services[key.name] = service

    def resolve(self, key: ServiceKey[T]) -> T:
        """Resolve a service with type safety."""
        with self._lock:
            if key.name in self._services:
                self._resolve_hits[key.name] = self._resolve_hits.get(key.name, 0) + 1
                return cast(T, self._services[key.name])
            elif key.name in self._factories:
                service = self._factories[key.name]()
                self._services[key.name] = service
                self._resolve_hits[key.name] = self._resolve_hits.get(key.name, 0) + 1
                return cast(T, service)
            raise KeyError(f"Service not found: {key.name}")

    def get(self, key: ServiceKey[T], default: T | None = None) -> T | None:
        """Get a service with optional default."""
        try:
            return self.resolve(key)
        except KeyError:
            return default

    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service is registered."""
        with self._lock:
            return key.name in self._services or key.name in self._factories

    def unregister(self, key: ServiceKey[T]) -> None:
        """Unregister a service."""
        with self._lock:
            self._services.pop(key.name, None)
            self._factories.pop(key.name, None)

    def clear(self) -> None:
        with self._lock:
            self._services.clear()
            self._factories.clear()

    def list_services(self) -> list[str]:
        with self._lock:
            return list(set(self._services.keys()) | set(self._factories.keys()))

    def report_unused(self) -> list[str]:
        """Return keys that were registered but never resolved."""
        with self._lock:
            registered = set(self._services) | set(self._factories)
            used = set(k for k, n in self._resolve_hits.items() if n > 0)
            return sorted(registered - used)

    def create_child(self, **services: object) -> ChildServiceRegistry:
        """Create a child registry with inheritance."""
        return ChildServiceRegistry(parent=self, **services)


class ChildServiceRegistry(ServiceRegistry):
    """Service registry with parent inheritance."""

    def __init__(self, parent: ServiceRegistry, **services: object) -> None:
        super().__init__()
        self._parent = parent

        for name, service in services.items():
            key = type("ServiceKey", (), {"name": name})()
            self.register(key, service)

    def resolve(self, key: ServiceKey[T]) -> T:
        """Resolve a service, checking parent if not found locally."""
        try:
            return super().resolve(key)
        except KeyError:
            return self._parent.resolve(key)

    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service is registered in self or parent."""
        return super().has(key) or self._parent.has(key)

    def has_local(self, key: ServiceKey[T]) -> bool:
        """Check if service exists in local registry only."""
        return super().has(key)
