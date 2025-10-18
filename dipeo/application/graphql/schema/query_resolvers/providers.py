"""Provider-related query resolvers and helpers."""

from typing import Any

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import INTEGRATED_API_SERVICE, PROVIDER_REGISTRY
from dipeo.diagram_generated.graphql.domain_types import (
    AuthConfigType,
    OperationSchemaType,
    OperationType,
    ProviderMetadataType,
    ProviderStatisticsType,
    ProviderType,
    RateLimitConfigType,
    RetryPolicyType,
)
from dipeo.infrastructure.integrations.drivers.integrated_api.generic_provider import (
    GenericHTTPProvider,
)
from dipeo.infrastructure.integrations.drivers.integrated_api.registry import ProviderRegistry


def _create_operation_type_from_provider(provider_instance: Any, op_name: str) -> OperationType:
    method, path, desc, scopes, pagination, timeout = "POST", f"/{op_name}", None, None, False, None

    if isinstance(provider_instance, GenericHTTPProvider):
        op_config = provider_instance.manifest.operations.get(op_name)
        if op_config:
            method, path, desc, scopes = (
                op_config.method,
                op_config.path,
                op_config.description,
                op_config.required_scopes,
            )
            pagination = op_config.pagination is not None and op_config.pagination.type != "none"
            timeout = op_config.timeout_override

    return OperationType(op_name, method, path, desc, scopes, pagination, timeout)


def _extract_provider_config(
    provider_instance: Any,
) -> tuple[str | None, AuthConfigType | None, RateLimitConfigType | None, RetryPolicyType | None]:
    if not isinstance(provider_instance, GenericHTTPProvider):
        return None, None, None, None

    manifest = provider_instance.manifest
    base_url = str(manifest.base_url)

    auth_config = None
    if manifest.auth:
        auth_config = AuthConfigType(
            strategy=manifest.auth.strategy.value,
            header=manifest.auth.header,
            query_param=manifest.auth.query_param,
            format=manifest.auth.format,
            scopes=manifest.auth.scopes,
        )

    rate_limit = None
    if manifest.rate_limit:
        rate_limit = RateLimitConfigType(
            algorithm=manifest.rate_limit.algorithm.value,
            capacity=manifest.rate_limit.capacity,
            refill_per_sec=manifest.rate_limit.refill_per_sec,
            window_size_sec=manifest.rate_limit.window_size_sec,
        )

    retry_policy = None
    if manifest.retry_policy:
        retry_policy = RetryPolicyType(
            strategy=manifest.retry_policy.strategy.value,
            max_retries=manifest.retry_policy.max_retries,
            base_delay_ms=manifest.retry_policy.base_delay_ms,
            max_delay_ms=manifest.retry_policy.max_delay_ms,
            retry_on_status=manifest.retry_policy.retry_on_status,
        )

    return base_url, auth_config, rate_limit, retry_policy


def _convert_to_provider_type(
    provider_info: dict[str, Any], provider_registry: ProviderRegistry | None = None
) -> ProviderType:
    metadata = provider_info.get("metadata", {})

    provider_metadata = ProviderMetadataType(
        version=metadata.get("version", "1.0.0"),
        type=metadata.get("type", "programmatic"),
        manifest_path=metadata.get("manifest_path"),
        description=metadata.get("description"),
        documentation_url=metadata.get("documentation_url"),
        support_email=metadata.get("support_email"),
    )

    operations = [
        OperationType(op_name, "POST", f"/{op_name}", None, None, False, None)
        for op_name in provider_info.get("operations", [])
    ]

    base_url, auth_config, rate_limit, retry_policy = None, None, None, None
    if provider_registry:
        provider_instance = provider_registry.get_provider(provider_info["name"])
        if provider_instance:
            base_url, auth_config, rate_limit, retry_policy = _extract_provider_config(
                provider_instance
            )

    return ProviderType(
        name=provider_info["name"],
        operations=operations,
        metadata=provider_metadata,
        base_url=base_url,
        auth_config=auth_config,
        rate_limit=rate_limit,
        retry_policy=retry_policy,
        default_timeout=30.0,
    )


async def _ensure_provider_registry(registry: ServiceRegistry) -> ProviderRegistry:
    provider_registry = registry.get(PROVIDER_REGISTRY)
    if provider_registry:
        return provider_registry

    integrated_api = registry.resolve(INTEGRATED_API_SERVICE)

    if hasattr(integrated_api, "initialize") and not getattr(integrated_api, "_initialized", False):
        await integrated_api.initialize()

    if hasattr(integrated_api, "provider_registry"):
        return integrated_api.provider_registry

    provider_registry = ProviderRegistry()
    await provider_registry.initialize()
    integrated_api.provider_registry = provider_registry
    return provider_registry


async def get_providers(registry: ServiceRegistry) -> list[ProviderType]:
    """List all providers."""
    provider_reg = await _ensure_provider_registry(registry)
    providers = []

    for name in provider_reg.list_providers():
        provider_info = provider_reg.get_provider_info(name)
        if provider_info:
            providers.append(_convert_to_provider_type(provider_info, provider_reg))

    return providers


async def get_provider(registry: ServiceRegistry, name: str) -> ProviderType | None:
    """Get a single provider by name."""
    provider_reg = await _ensure_provider_registry(registry)
    provider_info = provider_reg.get_provider_info(name)

    if provider_info:
        return _convert_to_provider_type(provider_info, provider_reg)

    return None


async def get_provider_operations(registry: ServiceRegistry, provider: str) -> list[OperationType]:
    """Get operations for a specific provider."""
    provider_reg = await _ensure_provider_registry(registry)
    provider_instance = provider_reg.get_provider(provider)

    if not provider_instance:
        return []

    return [
        _create_operation_type_from_provider(provider_instance, op_name)
        for op_name in provider_instance.supported_operations
    ]


async def get_operation_schema(
    registry: ServiceRegistry, provider: str, operation: str
) -> OperationSchemaType | None:
    """Get schema for a specific operation."""
    provider_reg = await _ensure_provider_registry(registry)
    provider_instance = provider_reg.get_provider(provider)

    if not provider_instance:
        return None

    if hasattr(provider_instance, "get_operation_schema"):
        schema = provider_instance.get_operation_schema(operation)
        if schema:
            return OperationSchemaType(
                operation=schema.get("operation", operation),
                method=schema.get("method", "POST"),
                path=schema.get("path", f"/{operation}"),
                description=schema.get("description"),
                request_body=schema.get("request_body"),
                query_params=schema.get("query_params"),
                response=schema.get("response"),
            )

    return OperationSchemaType(
        operation=operation,
        method="POST",
        path=f"/{operation}",
        description=None,
        request_body=None,
        query_params=None,
        response=None,
    )


async def get_provider_statistics(registry: ServiceRegistry) -> ProviderStatisticsType:
    """Get provider statistics."""
    provider_reg = await _ensure_provider_registry(registry)
    stats = provider_reg.get_statistics()

    return ProviderStatisticsType(
        total_providers=stats["total_providers"],
        total_operations=stats["total_operations"],
        provider_types=stats["provider_types"],
        providers=stats["providers"],
    )
