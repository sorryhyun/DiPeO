"""Integrated API service implementation."""

import logging
from typing import Any, Optional

from dipeo.core import BaseService, ServiceError
from dipeo.core.ports import IntegratedApiServicePort, ApiProviderPort
from dipeo.diagram_generated.enums import APIServiceType

from .providers.notion_provider import NotionProvider
from .providers.slack_provider import SlackProvider

logger = logging.getLogger(__name__)


class IntegratedApiService(BaseService, IntegratedApiServicePort):
    """Service that manages multiple API providers through a unified interface."""

    def __init__(self, api_service=None):
        super().__init__()
        self._providers: dict[str, ApiProviderPort] = {}
        self._api_service = api_service  # For providers that need APIService
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service and register default providers."""
        if self._initialized:
            return

        logger.info("Initializing IntegratedApiService")

        # Register default providers
        await self._register_default_providers()

        self._initialized = True

    async def _register_default_providers(self) -> None:
        """Register the default set of API providers."""
        # Register Notion provider
        notion_provider = NotionProvider()
        await self.register_provider(APIServiceType.NOTION.value, notion_provider)

        # Register Slack provider
        slack_provider = SlackProvider(api_service=self._api_service)
        await self.register_provider(APIServiceType.SLACK.value, slack_provider)

        # Additional providers can be registered here as they're implemented
        # Examples:
        # github_provider = GitHubProvider(api_service=self._api_service)
        # await self.register_provider(APIServiceType.GITHUB.value, github_provider)

    async def register_provider(self, provider_name: str, provider_instance: ApiProviderPort) -> None:
        """Register a new API provider."""
        if provider_name in self._providers:
            logger.warning(f"Provider '{provider_name}' already registered, overwriting")

        # Initialize the provider
        await provider_instance.initialize()

        self._providers[provider_name] = provider_instance
        logger.info(f"Registered provider '{provider_name}' with operations: {provider_instance.supported_operations}")

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

        # Get the provider
        provider_instance = self._providers.get(provider)
        if not provider_instance:
            available_providers = ", ".join(self._providers.keys())
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
        return list(self._providers.keys())

    def get_provider_operations(self, provider: str) -> list[str]:
        """Get supported operations for a specific provider."""
        provider_instance = self._providers.get(provider)
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
        provider_instance = self._providers.get(provider)
        if not provider_instance:
            return False

        # Check if operation is supported
        if operation not in provider_instance.supported_operations:
            return False

        # Validate configuration
        return await provider_instance.validate_config(operation, config)