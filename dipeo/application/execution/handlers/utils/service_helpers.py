"""Service resolution utilities for execution requests."""

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceKey, ServiceRegistry


def normalize_service_key(
    key: Union["ServiceKey", str],
) -> tuple["ServiceKey", str]:
    """Convert service key to (ServiceKey, name) tuple."""
    from dipeo.application.registry import ServiceKey

    if isinstance(key, str):
        return ServiceKey(key), key
    return key, key.name


def resolve_required_service(
    services: Union[dict[str, Any], "ServiceRegistry"],
    key: Union["ServiceKey", str],
) -> Any:
    """Resolve required service, raising KeyError if missing."""
    service_key, name = normalize_service_key(key)

    if isinstance(services, dict):
        if name not in services:
            raise KeyError(f"Required service '{name}' not found in service container")
        return services[name]
    else:
        return services.resolve(service_key)


def resolve_optional_service(
    services: Union[dict[str, Any], "ServiceRegistry"],
    key: Union["ServiceKey", str],
    default: Any = None,
) -> Any:
    """Resolve optional service, returning default if missing."""
    service_key, name = normalize_service_key(key)

    if isinstance(services, dict):
        return services.get(name, default)
    else:
        try:
            return services.resolve(service_key)
        except KeyError:
            return default


def has_service(
    services: Union[dict[str, Any], "ServiceRegistry"],
    key: Union["ServiceKey", str],
) -> bool:
    """Check if service exists in container."""
    service_key, name = normalize_service_key(key)

    if isinstance(services, dict):
        return name in services
    else:
        return services.has(service_key)
