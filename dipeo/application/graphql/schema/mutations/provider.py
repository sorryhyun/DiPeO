"""Provider integration mutation resolvers."""

import logging
import time
from typing import Any

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import API_KEY_SERVICE, INTEGRATED_API_SERVICE
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.graphql.domain_types import IntegrationTestResultType
from dipeo.diagram_generated.graphql.inputs import ExecuteIntegrationInput, TestIntegrationInput

logger = get_module_logger(__name__)


def _resolve_api_key(registry: ServiceRegistry, api_key_id: str | None) -> str | None:
    if not api_key_id:
        return None

    api_key_service = registry.resolve(API_KEY_SERVICE)
    key_data = api_key_service.get_api_key(str(api_key_id))
    return key_data.get("key") if key_data else None


async def execute_integration(registry: ServiceRegistry, input: ExecuteIntegrationInput) -> Any:
    """Execute an integration operation."""
    integrated_api = registry.resolve(INTEGRATED_API_SERVICE)
    api_key = _resolve_api_key(registry, input.api_key_id)

    try:
        result = await integrated_api.execute_operation(
            provider=input.provider,
            operation=input.operation,
            config=input.config,
            resource_id=input.resource_id,
            api_key=api_key,
            timeout=float(input.timeout) if input.timeout else 30.0,
        )
        return result
    except Exception as e:
        logger.error(f"Integration execution failed: {e}")
        raise


async def test_integration(
    registry: ServiceRegistry, input: TestIntegrationInput
) -> IntegrationTestResultType:
    """Test an integration operation."""
    start_time = time.time()

    try:
        if input.dry_run:
            integrated_api = registry.resolve(INTEGRATED_API_SERVICE)
            is_valid = await integrated_api.validate_operation(
                provider=input.provider, operation=input.operation, config=input.config_preview
            )
            return IntegrationTestResultType(
                success=is_valid,
                provider=input.provider,
                operation=input.operation,
                status_code=200 if is_valid else 400,
                response_time_ms=(time.time() - start_time) * 1000,
                error=None if is_valid else "Invalid configuration",
                response_preview={"validation": "passed" if is_valid else "failed"},
            )

        result = await execute_integration(
            registry,
            ExecuteIntegrationInput(
                provider=input.provider,
                operation=input.operation,
                config=input.config_preview,
                api_key_id=input.api_key_id,
                timeout=30,
            ),
        )
        return IntegrationTestResultType(
            success=True,
            provider=input.provider,
            operation=input.operation,
            status_code=200,
            response_time_ms=(time.time() - start_time) * 1000,
            error=None,
            response_preview=result,
        )

    except Exception as e:
        return IntegrationTestResultType(
            success=False,
            provider=input.provider,
            operation=input.operation,
            status_code=500,
            response_time_ms=(time.time() - start_time) * 1000,
            error=str(e),
            response_preview=None,
        )


async def reload_provider(registry: ServiceRegistry, name: str) -> bool:
    """Reload a provider (for manifest-based providers)."""
    from dipeo.application.graphql.schema.query_resolvers.providers import (
        _ensure_provider_registry,
    )

    provider_reg = await _ensure_provider_registry(registry)
    return await provider_reg.reload_provider(name)
