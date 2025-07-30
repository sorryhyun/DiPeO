"""Type-safe service registry for DiPeO application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Generic, Protocol, TypeVar, runtime_checkable, cast
import threading


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ServiceKey(Generic[T]):
    """Type-safe service key with compile-time type guarantees."""
    
    name: str
    
    def __class_getitem__(cls, item):
        """Enable ServiceKey[ServiceType] syntax for type hints only.
        
        This is purely for static type checking. The actual type parameter
        is not used at runtime to avoid circular import issues.
        """
        # Return a new class that inherits from ServiceKey
        # This allows type checkers to understand ServiceKey[T]
        return cls
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"ServiceKey[{self.name}]"


class ServiceRegistry:
    """Thread-safe service registry with type guarantees."""
    
    def __init__(self) -> None:
        self._services: Dict[str, object] = {}
        self._factories: Dict[str, Callable[[], object]] = {}
        self._lock = threading.RLock()
    
    def register(self, key: ServiceKey[T], service: T | Callable[[], T]) -> None:
        """Register a service or factory.
        
        Args:
            key: Type-safe service key
            service: Service instance or factory function
        """
        with self._lock:
            if callable(service) and not hasattr(service, "__self__"):
                # It's a factory function
                self._factories[key.name] = service
            else:
                # It's a service instance
                self._services[key.name] = service
    
    def resolve(self, key: ServiceKey[T]) -> T:
        """Resolve a service with type safety.
        
        Args:
            key: Type-safe service key
            
        Returns:
            The service instance
            
        Raises:
            KeyError: If service not found
        """
        with self._lock:
            if key.name in self._services:
                return cast(T, self._services[key.name])
            elif key.name in self._factories:
                # Create service from factory and cache it
                service = self._factories[key.name]()
                self._services[key.name] = service
                return cast(T, service)
            raise KeyError(f"Service not found: {key.name}")
    
    def get(self, key: ServiceKey[T], default: T | None = None) -> T | None:
        """Get a service with optional default.
        
        Args:
            key: Type-safe service key
            default: Default value if not found
            
        Returns:
            The service instance or default
        """
        try:
            return self.resolve(key)
        except KeyError:
            return default
    
    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service is registered.
        
        Args:
            key: Type-safe service key
            
        Returns:
            True if service is registered
        """
        with self._lock:
            return key.name in self._services or key.name in self._factories
    
    def unregister(self, key: ServiceKey[T]) -> None:
        """Unregister a service.
        
        Args:
            key: Type-safe service key
        """
        with self._lock:
            self._services.pop(key.name, None)
            self._factories.pop(key.name, None)
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
    
    def list_services(self) -> list[str]:
        """List all registered service names."""
        with self._lock:
            return list(set(self._services.keys()) | set(self._factories.keys()))
    
    def create_child(self, **services: object) -> ChildServiceRegistry:
        """Create a child registry with inheritance.
        
        Args:
            **services: Initial services for child
            
        Returns:
            New child registry with parent inheritance
        """
        return ChildServiceRegistry(parent=self, **services)


class ChildServiceRegistry(ServiceRegistry):
    """Service registry with parent inheritance."""
    
    def __init__(self, parent: ServiceRegistry, **services: object) -> None:
        super().__init__()
        self._parent = parent
        
        # Register initial services
        for name, service in services.items():
            # Create a simple key for initial services
            key = type("ServiceKey", (), {"name": name})()
            self.register(key, service)
    
    def resolve(self, key: ServiceKey[T]) -> T:
        """Resolve a service, checking parent if not found locally.
        
        Args:
            key: Type-safe service key
            
        Returns:
            The service instance
            
        Raises:
            KeyError: If service not found in self or parent
        """
        try:
            return super().resolve(key)
        except KeyError:
            # Try parent registry
            return self._parent.resolve(key)
    
    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service is registered in self or parent.
        
        Args:
            key: Type-safe service key
            
        Returns:
            True if service is registered
        """
        return super().has(key) or self._parent.has(key)
    
    def has_local(self, key: ServiceKey[T]) -> bool:
        """Check if service exists in local registry only.
        
        Args:
            key: Type-safe service key
            
        Returns:
            True if exists locally
        """
        return super().has(key)