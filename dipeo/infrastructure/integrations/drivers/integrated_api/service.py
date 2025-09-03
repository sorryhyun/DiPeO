"""Integrated API service implementation."""

import logging
from typing import Any, Optional
from pathlib import Path

from dipeo.domain.base import BaseService, ServiceError
from dipeo.domain.integrations.ports import ApiInvoker as IntegratedApiServicePort
from dipeo.domain.integrations.ports import ApiProvider as ApiProviderPort
from dipeo.domain.integrations.ports import APIKeyPort

from .registry import ProviderRegistry
from .generic_provider import GenericHTTPProvider

logger = logging.getLogger(__name__)


class IntegratedApiService(BaseService, IntegratedApiServicePort):
    """Service that manages multiple API providers through a unified interface."""

    def __init__(self, api_service=None, api_key_port: Optional[APIKeyPort] = None):
        super().__init__()
        self._api_service = api_service  # For providers that need APIService
        self._api_key_port = api_key_port  # For resolving API keys
        self.provider_registry = ProviderRegistry()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service and register default providers."""
        if self._initialized:
            return

        logger.info("Initializing IntegratedApiService")

        # Initialize the provider registry
        await self.provider_registry.initialize()

        # Load manifest-based providers if configured
        await self._load_manifest_providers()

        # Load providers from entry points
        await self._load_entrypoint_providers()
        
        # Load MCP providers
        await self._load_mcp_providers()

        self._initialized = True

    async def _load_manifest_providers(self) -> None:
        """Load manifest-based providers from the filesystem."""
        # Look for provider manifests in standard locations
        manifest_locations = [
            "integrations/**/provider.yaml",
            "integrations/**/provider.yml",
            "integrations/**/provider.json",
        ]
        
        for pattern in manifest_locations:
            try:
                await self.provider_registry.load_manifests(pattern)
            except Exception as e:
                logger.debug(f"No manifests found at {pattern}: {e}")
    
    async def _load_entrypoint_providers(self) -> None:
        """Load providers from Python package entry points."""
        try:
            await self.provider_registry.load_entrypoints("dipeo.integrations")
        except Exception as e:
            logger.debug(f"No entry point providers found: {e}")
    
    async def _load_mcp_providers(self) -> None:
        """Load MCP (Model Context Protocol) providers."""
        try:
            from .mcp_registry import get_mcp_registry
            
            logger.info("Loading MCP providers")
            
            # Get the MCP registry and initialize it
            mcp_registry = await get_mcp_registry()
            
            # Create an MCP provider with all registered tools
            mcp_provider = mcp_registry.create_provider("mcp")
            
            # Register the MCP provider with the main registry
            await self.provider_registry.register(
                "mcp",
                mcp_provider,
                metadata={
                    "type": "mcp",
                    "description": "MCP Tool Provider",
                    "tools_count": len(mcp_provider.supported_operations)
                }
            )
            
            # Also register individual MCP tool providers if they exist
            # This allows using specific tool sets like mcp_browser, mcp_filesystem
            for category in ["browser", "filesystem"]:
                category_tools = mcp_registry.get_tools_by_category(category)
                if category_tools:
                    from .providers.mcp_provider import MCPProvider
                    category_provider = MCPProvider(
                        provider_name=f"mcp_{category}",
                        tools=category_tools
                    )
                    await category_provider.initialize()
                    await self.provider_registry.register(
                        f"mcp_{category}",
                        category_provider,
                        metadata={
                            "type": "mcp",
                            "category": category,
                            "description": f"MCP {category.title()} Tools",
                            "tools_count": len(category_tools)
                        }
                    )
            
            logger.info(f"Loaded MCP providers with {len(mcp_provider.supported_operations)} tools")
            
        except ImportError as e:
            logger.debug(f"MCP providers not available: {e}")
        except Exception as e:
            logger.error(f"Error loading MCP providers: {e}")

    async def register_provider(self, provider_name: str, provider_instance: ApiProviderPort) -> None:
        """Register a new API provider.
        
        This method is kept for backward compatibility.
        New code should use provider_registry.register() directly.
        """
        await self.provider_registry.register(provider_name, provider_instance)

    async def execute_operation(
        self,
        provider: str,
        operation: str,
        config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> dict[str, Any]:
        """Execute an operation on a specific provider."""
        # Ensure service is initialized
        if not self._initialized:
            await self.initialize()

        # Get the provider from registry
        provider_instance = self.provider_registry.get_provider(provider)
        if not provider_instance:
            available_providers = ", ".join(self.provider_registry.list_providers())
            raise ValueError(
                f"Provider '{provider}' not registered. "
                f"Available providers: {available_providers}"
            )

        # Validate the operation
        if operation not in provider_instance.supported_operations:
            supported_ops = ", ".join(provider_instance.supported_operations)
            raise ValueError(
                f"Operation '{operation}' not supported by provider '{provider}'. "
                f"Supported operations: {supported_ops}"
            )

        # For GenericHTTPProvider, ensure it has access to APIService and APIKeyPort
        if isinstance(provider_instance, GenericHTTPProvider):
            if not provider_instance.api_service:
                provider_instance.api_service = self._api_service
            if not provider_instance.api_key_port:
                provider_instance.api_key_port = self._api_key_port

        # Execute the operation with retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                return await provider_instance.execute(
                    operation=operation,
                    config=config,
                    resource_id=resource_id,
                    api_key=api_key,
                    timeout=timeout
                )
            except ServiceError:
                # Don't retry on service errors (usually validation issues)
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    # Simple exponential backoff could be added here
                    continue

        # If we get here, all retries failed
        raise ServiceError(
            f"Operation '{operation}' on provider '{provider}' failed after "
            f"{max_retries} attempts: {last_error}"
        )

    def get_supported_providers(self) -> list[str]:
        """Get list of currently registered providers."""
        return self.provider_registry.list_providers()

    def get_provider_operations(self, provider: str) -> list[str]:
        """Get supported operations for a specific provider."""
        provider_instance = self.provider_registry.get_provider(provider)
        if not provider_instance:
            raise ValueError(f"Provider '{provider}' not registered")

        return provider_instance.supported_operations

    async def validate_operation(
        self,
        provider: str,
        operation: str,
        config: dict[str, Any] | None = None
    ) -> bool:
        """Validate if an operation is supported and properly configured."""
        # Check if provider exists
        provider_instance = self.provider_registry.get_provider(provider)
        if not provider_instance:
            return False

        # Check if operation is supported
        if operation not in provider_instance.supported_operations:
            return False

        # Validate configuration
        return await provider_instance.validate_config(operation, config)