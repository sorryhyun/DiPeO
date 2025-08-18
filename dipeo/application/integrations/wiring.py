"""Wiring module for integrations bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey

if TYPE_CHECKING:
    from dipeo.application.integrations.use_cases.manage_api_keys import APIKeyService
    from dipeo.domain.integrations import ApiInvoker, ApiProviderRegistry

logger = logging.getLogger(__name__)

# Define service keys for integrations context
API_KEY_SERVICE_KEY = ServiceKey["APIKeyService"]("integrations.api_key_service")
API_INVOKER_KEY = ServiceKey["ApiInvoker"]("integrations.api_invoker")
PROVIDER_REGISTRY_KEY = ServiceKey["ApiProviderRegistry"]("integrations.provider_registry")
CALL_API_USE_CASE = ServiceKey["CallExternalAPI"]("integrations.use_case.call_api")
VALIDATE_KEY_USE_CASE = ServiceKey["ValidateAPIKey"]("integrations.use_case.validate_key")


def wire_integrations(registry: ServiceRegistry) -> None:
    """Wire integrations bounded context services and use cases.
    
    This includes:
    - API key management service
    - API invoker
    - API provider registry
    - External service adapters
    """
    logger.info("🔧 Wiring integrations bounded context")
    
    # Wire API key service
    from dipeo.application.integrations.use_cases.manage_api_keys import APIKeyService
    from dipeo.application.registry.registry_tokens import API_KEY_SERVICE
    
    def create_api_key_service() -> APIKeyService:
        """Factory for API key service."""
        return APIKeyService(registry=registry)
    
    registry.register(API_KEY_SERVICE, create_api_key_service)
    registry.register(API_KEY_SERVICE_KEY, create_api_key_service)
    
    # Wire API invoker (from infrastructure)
    from dipeo.application.registry.registry_tokens import API_INVOKER
    
    def create_api_invoker():
        """Factory for API invoker."""
        # Check if V2 is enabled
        import os
        use_v2 = os.getenv("INTEGRATIONS_PORT_V2", "0") == "1"
        
        if use_v2:
            from dipeo.infrastructure.integrations.adapters.api_invoker import HttpApiInvoker
            from dipeo.infrastructure.integrations.drivers.http_client import HttpClient
            from dipeo.infrastructure.integrations.drivers.rate_limiter import RateLimiter
            from dipeo.infrastructure.integrations.drivers.manifest_registry import ManifestRegistry
            
            http_client = HttpClient()
            rate_limiter = RateLimiter()
            manifest_registry = ManifestRegistry()
            
            return HttpApiInvoker(
                http=http_client,
                limiter=rate_limiter,
                manifests=manifest_registry
            )
        else:
            # Use existing integrated API service
            from dipeo.infrastructure.integrations.drivers.integrated_api_service import IntegratedAPIService
            api_key_service = registry.resolve(API_KEY_SERVICE)
            return IntegratedAPIService(api_key_service=api_key_service)
    
    registry.register(API_INVOKER, create_api_invoker)
    registry.register(API_INVOKER_KEY, create_api_invoker)
    
    # Wire API provider registry
    from dipeo.application.registry.registry_tokens import API_PROVIDER_REGISTRY
    
    def create_api_provider_registry():
        """Factory for API provider registry."""
        from dipeo.infrastructure.integrations.drivers.api_provider_registry import APIProviderRegistry
        return APIProviderRegistry()
    
    registry.register(API_PROVIDER_REGISTRY, create_api_provider_registry)
    registry.register(PROVIDER_REGISTRY_KEY, create_api_provider_registry)
    
    # Wire additional integration use cases
    wire_integration_use_cases(registry)
    
    logger.info("✅ Integrations bounded context wired")


def wire_integration_use_cases(registry: ServiceRegistry) -> None:
    """Wire additional integration-specific use cases."""
    from dipeo.application.registry.registry_tokens import API_INVOKER, API_KEY_SERVICE
    
    # Wire external API call use case
    def create_call_external_api():
        """Factory for external API call use case."""
        api_invoker = registry.resolve(API_INVOKER)
        
        class CallExternalAPI:
            def __init__(self):
                self.api_invoker = api_invoker
            
            async def execute(self, provider: str, endpoint: str, params: dict) -> dict:
                """Execute an external API call."""
                from dipeo.domain.integrations import ApiRequest
                request = ApiRequest(
                    provider=provider,
                    endpoint=endpoint,
                    params=params
                )
                response = await self.api_invoker.invoke(request)
                return response.data
        
        return CallExternalAPI()
    
    registry.register(CALL_API_USE_CASE, create_call_external_api)
    
    # Wire API key validation use case
    def create_validate_api_key():
        """Factory for API key validation use case."""
        api_key_service = registry.resolve(API_KEY_SERVICE)
        
        class ValidateAPIKey:
            def __init__(self):
                self.api_key_service = api_key_service
            
            async def execute(self, provider: str, key: str) -> bool:
                """Validate an API key for a provider."""
                return await self.api_key_service.validate_key(provider, key)
        
        return ValidateAPIKey()
    
    registry.register(VALIDATE_KEY_USE_CASE, create_validate_api_key)