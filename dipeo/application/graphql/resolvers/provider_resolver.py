"""GraphQL resolver for API provider queries and mutations."""

import logging
from typing import List, Optional, Any
import time

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import INTEGRATED_API_SERVICE, API_KEY_SERVICE
from dipeo.core import ServiceError
from dipeo.infrastructure.services.integrated_api.registry import ProviderRegistry
from dipeo.infrastructure.services.integrated_api.generic_provider import GenericHTTPProvider

from ..types.provider_types import (
    ProviderType,
    OperationType,
    ProviderMetadataType,
    OperationSchemaType,
    AuthConfigType,
    RateLimitConfigType,
    RetryPolicyType,
    ProviderStatisticsType,
    IntegrationTestResultType,
    ExecuteIntegrationInput,
    TestIntegrationInput
)

logger = logging.getLogger(__name__)


class ProviderResolver:
    """Resolves provider-related GraphQL queries and mutations."""
    
    def __init__(self, registry: ServiceRegistry):
        """Initialize provider resolver.
        
        Args:
            registry: Service registry for accessing services
        """
        self.registry = registry
        self._provider_registry: Optional[ProviderRegistry] = None
    
    async def _ensure_provider_registry(self) -> ProviderRegistry:
        """Ensure provider registry is available.
        
        Returns:
            Provider registry instance
        """
        if not self._provider_registry:
            # Get the integrated API service
            integrated_api = await self.registry.resolve(INTEGRATED_API_SERVICE)
            
            # Check if it has a registry attribute
            if hasattr(integrated_api, 'provider_registry'):
                self._provider_registry = integrated_api.provider_registry
            else:
                # Create a new registry if not available
                self._provider_registry = ProviderRegistry()
                await self._provider_registry.initialize()
                
                # Attach to integrated API service for future use
                integrated_api.provider_registry = self._provider_registry
        
        return self._provider_registry
    
    async def list_providers(self) -> List[ProviderType]:
        """List all registered providers.
        
        Returns:
            List of provider information
        """
        registry = await self._ensure_provider_registry()
        providers = []
        
        for name in registry.list_providers():
            provider_info = registry.get_provider_info(name)
            if provider_info:
                providers.append(self._convert_to_graphql_type(provider_info))
        
        return providers
    
    async def get_provider(self, name: str) -> Optional[ProviderType]:
        """Get a specific provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider information or None
        """
        registry = await self._ensure_provider_registry()
        provider_info = registry.get_provider_info(name)
        
        if provider_info:
            return self._convert_to_graphql_type(provider_info)
        
        return None
    
    async def get_provider_operations(self, provider: str) -> List[OperationType]:
        """Get operations for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of operations
        """
        registry = await self._ensure_provider_registry()
        provider_instance = registry.get_provider(provider)
        
        if not provider_instance:
            return []
        
        operations = []
        for op_name in provider_instance.supported_operations:
            # Get operation details if available
            op_info = OperationType(
                name=op_name,
                method="POST",  # Default, would be from manifest
                path=f"/{op_name}",  # Default path
                description=None,
                required_scopes=None,
                has_pagination=False,
                timeout_override=None
            )
            
            # If it's a generic provider, get more details
            if isinstance(provider_instance, GenericHTTPProvider):
                op_config = provider_instance.manifest.operations.get(op_name)
                if op_config:
                    op_info.method = op_config.method
                    op_info.path = op_config.path
                    op_info.description = op_config.description
                    op_info.required_scopes = op_config.required_scopes
                    op_info.has_pagination = (
                        op_config.pagination is not None and 
                        op_config.pagination.type != "none"
                    )
                    op_info.timeout_override = op_config.timeout_override
            
            operations.append(op_info)
        
        return operations
    
    async def get_operation_schema(
        self,
        provider: str,
        operation: str
    ) -> Optional[OperationSchemaType]:
        """Get schema for a specific operation.
        
        Args:
            provider: Provider name
            operation: Operation name
            
        Returns:
            Operation schema or None
        """
        registry = await self._ensure_provider_registry()
        provider_instance = registry.get_provider(provider)
        
        if not provider_instance:
            return None
        
        # Check if provider has schema method
        if hasattr(provider_instance, 'get_operation_schema'):
            schema = provider_instance.get_operation_schema(operation)
            if schema:
                return OperationSchemaType(
                    operation=schema.get('operation', operation),
                    method=schema.get('method', 'POST'),
                    path=schema.get('path', f'/{operation}'),
                    description=schema.get('description'),
                    request_body=schema.get('request_body'),
                    query_params=schema.get('query_params'),
                    response=schema.get('response')
                )
        
        # Default schema
        return OperationSchemaType(
            operation=operation,
            method='POST',
            path=f'/{operation}',
            description=None,
            request_body=None,
            query_params=None,
            response=None
        )
    
    async def get_provider_statistics(self) -> ProviderStatisticsType:
        """Get statistics about registered providers.
        
        Returns:
            Provider statistics
        """
        registry = await self._ensure_provider_registry()
        stats = registry.get_statistics()
        
        return ProviderStatisticsType(
            total_providers=stats['total_providers'],
            total_operations=stats['total_operations'],
            provider_types=stats['provider_types'],
            providers=stats['providers']
        )
    
    async def execute_integration(
        self,
        input: ExecuteIntegrationInput
    ) -> Any:
        """Execute an integration operation.
        
        Args:
            input: Execution input
            
        Returns:
            Operation result
        """
        integrated_api = await self.registry.resolve(INTEGRATED_API_SERVICE)
        
        # Resolve API key if provided
        api_key = None
        if input.api_key_id:
            api_key_service = await self.registry.resolve(API_KEY_SERVICE)
            key_data = api_key_service.get_api_key(str(input.api_key_id))
            if key_data:
                api_key = key_data.get('key')
        
        try:
            result = await integrated_api.execute_operation(
                provider=input.provider,
                operation=input.operation,
                config=input.config,
                resource_id=input.resource_id,
                api_key=api_key,
                timeout=float(input.timeout) if input.timeout else 30.0
            )
            return result
        except Exception as e:
            logger.error(f"Integration execution failed: {e}")
            raise
    
    async def test_integration(
        self,
        input: TestIntegrationInput
    ) -> IntegrationTestResultType:
        """Test an integration operation.
        
        Args:
            input: Test input
            
        Returns:
            Test result
        """
        start_time = time.time()
        
        try:
            if input.dry_run:
                # Just validate the configuration
                integrated_api = await self.registry.resolve(INTEGRATED_API_SERVICE)
                is_valid = await integrated_api.validate_operation(
                    provider=input.provider,
                    operation=input.operation,
                    config=input.config_preview
                )
                
                return IntegrationTestResultType(
                    success=is_valid,
                    provider=input.provider,
                    operation=input.operation,
                    status_code=200 if is_valid else 400,
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=None if is_valid else "Invalid configuration",
                    response_preview={"validation": "passed" if is_valid else "failed"}
                )
            else:
                # Actually execute the operation
                result = await self.execute_integration(
                    ExecuteIntegrationInput(
                        provider=input.provider,
                        operation=input.operation,
                        config=input.config_preview,
                        api_key_id=input.api_key_id,
                        timeout=30
                    )
                )
                
                return IntegrationTestResultType(
                    success=True,
                    provider=input.provider,
                    operation=input.operation,
                    status_code=200,
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=None,
                    response_preview=result
                )
        except Exception as e:
            return IntegrationTestResultType(
                success=False,
                provider=input.provider,
                operation=input.operation,
                status_code=500,
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
                response_preview=None
            )
    
    async def reload_provider(self, name: str) -> bool:
        """Reload a provider (for manifest-based providers).
        
        Args:
            name: Provider name
            
        Returns:
            True if reloaded successfully
        """
        registry = await self._ensure_provider_registry()
        return await registry.reload_provider(name)
    
    def _convert_to_graphql_type(self, provider_info: dict[str, Any]) -> ProviderType:
        """Convert provider info to GraphQL type.
        
        Args:
            provider_info: Provider information dictionary
            
        Returns:
            GraphQL ProviderType
        """
        metadata = provider_info.get('metadata', {})
        
        # Convert metadata
        provider_metadata = ProviderMetadataType(
            version=metadata.get('version', '1.0.0'),
            type=metadata.get('type', 'programmatic'),
            manifest_path=metadata.get('manifest_path'),
            description=metadata.get('description'),
            documentation_url=metadata.get('documentation_url'),
            support_email=metadata.get('support_email')
        )
        
        # Convert operations
        operations = []
        for op_name in provider_info.get('operations', []):
            operations.append(
                OperationType(
                    name=op_name,
                    method='POST',  # Default
                    path=f'/{op_name}',
                    description=None,
                    required_scopes=None,
                    has_pagination=False,
                    timeout_override=None
                )
            )
        
        # Get additional config if available
        auth_config = None
        rate_limit = None
        retry_policy = None
        base_url = None
        
        # Try to get more details from the actual provider
        registry = self._provider_registry
        if registry:
            provider_instance = registry.get_provider(provider_info['name'])
            if isinstance(provider_instance, GenericHTTPProvider):
                manifest = provider_instance.manifest
                
                # Extract base URL
                base_url = str(manifest.base_url)
                
                # Extract auth config
                if manifest.auth:
                    auth_config = AuthConfigType(
                        strategy=manifest.auth.strategy.value,
                        header=manifest.auth.header,
                        query_param=manifest.auth.query_param,
                        format=manifest.auth.format,
                        scopes=manifest.auth.scopes
                    )
                
                # Extract rate limit
                if manifest.rate_limit:
                    rate_limit = RateLimitConfigType(
                        algorithm=manifest.rate_limit.algorithm.value,
                        capacity=manifest.rate_limit.capacity,
                        refill_per_sec=manifest.rate_limit.refill_per_sec,
                        window_size_sec=manifest.rate_limit.window_size_sec
                    )
                
                # Extract retry policy
                if manifest.retry_policy:
                    retry_policy = RetryPolicyType(
                        strategy=manifest.retry_policy.strategy.value,
                        max_retries=manifest.retry_policy.max_retries,
                        base_delay_ms=manifest.retry_policy.base_delay_ms,
                        max_delay_ms=manifest.retry_policy.max_delay_ms,
                        retry_on_status=manifest.retry_policy.retry_on_status
                    )
        
        return ProviderType(
            name=provider_info['name'],
            operations=operations,
            metadata=provider_metadata,
            base_url=base_url,
            auth_config=auth_config,
            rate_limit=rate_limit,
            retry_policy=retry_policy,
            default_timeout=30.0
        )