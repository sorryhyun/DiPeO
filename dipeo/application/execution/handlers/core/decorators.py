"""Decorators for handler service injection and dependency management."""

import functools
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar, Union

from dipeo.application.registry import ServiceKey

T = TypeVar("T")


class ServiceRequirement(Enum):
    """Service requirement levels for dependency injection."""

    REQUIRED = "required"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class ServiceSpec:
    """Specification for a service dependency."""

    key: Union[ServiceKey, str]
    requirement: ServiceRequirement = ServiceRequirement.REQUIRED
    default: Any = None


def requires_services(
    **service_specs: Union[ServiceKey, str, tuple[Union[ServiceKey, str], ServiceRequirement]],
):
    """Decorator to declare handler service dependencies.

    This decorator allows handlers to declaratively specify their service dependencies,
    which will be automatically injected at execution time.

    Usage:
        @requires_services(
            llm_service=LLM_SERVICE,  # Required service
            filesystem=(FILESYSTEM_ADAPTER, ServiceRequirement.OPTIONAL),  # Optional service
        )
        class MyHandler(TypedNodeHandler):
            async def execute_request(self, request, **services):
                llm = services['llm_service']  # Guaranteed to exist
                fs = services.get('filesystem')  # May be None

    Args:
        **service_specs: Keyword arguments mapping service names to either:
            - A ServiceKey or string (implies REQUIRED)
            - A tuple of (ServiceKey/string, ServiceRequirement)

    Returns:
        Decorator function that adds service requirements to the handler class
    """

    def decorator(cls):
        parsed_specs = {}
        for name, spec in service_specs.items():
            if isinstance(spec, tuple):
                # Tuple format: (key, requirement)
                key, requirement = spec
                if not isinstance(requirement, ServiceRequirement):
                    requirement = ServiceRequirement.REQUIRED
                parsed_specs[name] = ServiceSpec(key, requirement)
            else:
                # Single value: implies required
                parsed_specs[name] = ServiceSpec(spec, ServiceRequirement.REQUIRED)

        cls._service_requirements = parsed_specs
        original_run = cls.run

        @functools.wraps(original_run)
        async def wrapped_run(self, inputs, request, *args, **kwargs):
            services = {}

            for name, spec in parsed_specs.items():
                if spec.requirement == ServiceRequirement.REQUIRED:
                    try:
                        services[name] = request.get_required_service(spec.key)
                    except KeyError as e:
                        raise RuntimeError(
                            f"{cls.__name__} requires service '{name}' ({spec.key}) but it was not found"
                        ) from e
                else:
                    services[name] = request.get_optional_service(spec.key, spec.default)

            # Store services as instance attributes for use in the handler
            for name, service in services.items():
                setattr(self, f"_{name}", service)

            return await original_run(self, inputs, request, *args, **kwargs)

        cls.run = wrapped_run

        # Also add a method to get required service names (useful for validation)
        cls.get_required_services = classmethod(
            lambda cls: [
                name
                for name, spec in parsed_specs.items()
                if spec.requirement == ServiceRequirement.REQUIRED
            ]
        )

        cls.get_optional_services = classmethod(
            lambda cls: [
                name
                for name, spec in parsed_specs.items()
                if spec.requirement == ServiceRequirement.OPTIONAL
            ]
        )

        return cls

    return decorator


Required = ServiceRequirement.REQUIRED
Optional = ServiceRequirement.OPTIONAL
