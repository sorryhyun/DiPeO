"""Authentication strategy implementations for API providers."""

import base64
import logging
from abc import ABC, abstractmethod
from typing import Any

from jinja2 import Template

from dipeo.domain.base.exceptions import ServiceError
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.infrastructure.integrations.drivers.integrated_api.manifest_schema import (
    AuthConfig,
    AuthStrategy,
)

logger = logging.getLogger(__name__)


class BaseAuthStrategy(ABC):
    """Base class for authentication strategies."""

    def __init__(self, auth_config: AuthConfig, api_key_port: APIKeyPort | None = None):
        """Initialize auth strategy.

        Args:
            auth_config: Authentication configuration
            api_key_port: Port for resolving API keys
        """
        self.auth_config = auth_config
        self.api_key_port = api_key_port

    @abstractmethod
    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Get authentication headers.

        Args:
            api_key: API key or credential
            context: Template context

        Returns:
            Dictionary of auth headers
        """
        pass

    async def get_auth_params(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Get authentication query parameters.

        Args:
            api_key: API key or credential
            context: Template context

        Returns:
            Dictionary of auth query parameters
        """
        return {}

    async def resolve_secret(self, api_key: str) -> dict[str, Any]:
        """Resolve API key to actual secret values.

        Args:
            api_key: API key identifier

        Returns:
            Secret values dictionary
        """
        if not self.api_key_port:
            return {"token": api_key, "api_key": api_key}

        try:
            key_data = await self.api_key_port.get_api_key(api_key)
            if not key_data:
                raise ServiceError(f"API key not found: {api_key}")

            return {
                "token": key_data.get("secret", api_key),
                "api_key": key_data.get("secret", api_key),
                "client_id": key_data.get("client_id"),
                "client_secret": key_data.get("client_secret"),
                "username": key_data.get("username"),
                "password": key_data.get("password"),
                **key_data.get("extra", {}),
            }
        except Exception as e:
            logger.error(f"Failed to resolve API key: {e}")
            return {"token": api_key, "api_key": api_key}


class NoAuthStrategy(BaseAuthStrategy):
    """No authentication required."""

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """No auth headers needed."""
        return {}


class ApiKeyHeaderStrategy(BaseAuthStrategy):
    """API key in header authentication."""

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Add API key to headers.

        Args:
            api_key: API key
            context: Template context

        Returns:
            Headers with API key
        """
        if not api_key:
            raise ServiceError("API key required for authentication")

        secret = await self.resolve_secret(api_key)
        context["secret"] = secret

        header_name = self.auth_config.header or "X-API-Key"

        if self.auth_config.format:
            template = Template(self.auth_config.format)
            header_value = template.render(**context)
        else:
            header_value = secret.get("api_key", api_key)

        return {header_name: header_value}


class ApiKeyQueryStrategy(BaseAuthStrategy):
    """API key in query parameter authentication."""

    async def get_auth_params(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Add API key to query parameters.

        Args:
            api_key: API key
            context: Template context

        Returns:
            Query parameters with API key
        """
        if not api_key:
            raise ServiceError("API key required for authentication")

        secret = await self.resolve_secret(api_key)
        context["secret"] = secret

        param_name = self.auth_config.query_param or "api_key"

        if self.auth_config.format:
            template = Template(self.auth_config.format)
            param_value = template.render(**context)
        else:
            param_value = secret.get("api_key", api_key)

        return {param_name: param_value}

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """No headers needed for query param auth."""
        return {}


class OAuth2BearerStrategy(BaseAuthStrategy):
    """OAuth2 Bearer token authentication."""

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Add Bearer token to Authorization header.

        Args:
            api_key: API key (contains token)
            context: Template context

        Returns:
            Headers with Bearer token
        """
        if not api_key:
            raise ServiceError("API key (token) required for OAuth2 authentication")

        secret = await self.resolve_secret(api_key)
        context["secret"] = secret

        header_name = self.auth_config.header or "Authorization"

        if self.auth_config.format:
            template = Template(self.auth_config.format)
            header_value = template.render(**context)
        else:
            token = secret.get("token", api_key)
            header_value = f"Bearer {token}"

        return {header_name: header_value}


class BasicAuthStrategy(BaseAuthStrategy):
    """HTTP Basic authentication."""

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Add Basic auth to Authorization header.

        Args:
            api_key: API key (contains username/password)
            context: Template context

        Returns:
            Headers with Basic auth
        """
        if not api_key:
            raise ServiceError("Credentials required for Basic authentication")

        secret = await self.resolve_secret(api_key)
        context["secret"] = secret

        username = secret.get("username", "")
        password = secret.get("password", "")

        if not username or not password:
            raise ServiceError("Username and password required for Basic authentication")

        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()

        header_name = self.auth_config.header or "Authorization"

        if self.auth_config.format:
            context["secret"]["encoded"] = encoded
            template = Template(self.auth_config.format)
            header_value = template.render(**context)
        else:
            header_value = f"Basic {encoded}"

        return {header_name: header_value}


class OAuth2ClientCredentialsStrategy(BaseAuthStrategy):
    """OAuth2 Client Credentials flow authentication.

    This is a simplified implementation. Full implementation would:
    1. Exchange client credentials for access token
    2. Cache the token until expiry
    3. Refresh when needed
    """

    def __init__(self, auth_config: AuthConfig, api_key_port: APIKeyPort | None = None):
        super().__init__(auth_config, api_key_port)
        self._token_cache = {}

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Get OAuth2 access token and add to headers.

        Args:
            api_key: API key (contains client credentials)
            context: Template context

        Returns:
            Headers with access token
        """
        if not api_key:
            raise ServiceError("Client credentials required for OAuth2 authentication")

        secret = await self.resolve_secret(api_key)

        cache_key = f"{secret.get('client_id')}:{self.auth_config.token_endpoint}"
        if cache_key in self._token_cache:
            access_token = self._token_cache[cache_key]
        else:
            access_token = await self._exchange_for_token(secret)
            self._token_cache[cache_key] = access_token

        context["secret"] = {**secret, "access_token": access_token}

        header_name = self.auth_config.header or "Authorization"

        if self.auth_config.format:
            template = Template(self.auth_config.format)
            header_value = template.render(**context)
        else:
            header_value = f"Bearer {access_token}"

        return {header_name: header_value}

    async def _exchange_for_token(self, secret: dict[str, Any]) -> str:
        """Exchange client credentials for access token.

        Args:
            secret: Secret containing client credentials

        Returns:
            Access token
        """
        logger.warning(
            "OAuth2 Client Credentials flow not fully implemented. " "Using client_secret as token."
        )
        return secret.get("client_secret", "")


class CustomAuthStrategy(BaseAuthStrategy):
    """Custom authentication strategy using a Python handler."""

    async def get_auth_headers(self, api_key: str, context: dict[str, Any]) -> dict[str, str]:
        """Call custom handler for auth headers.

        Args:
            api_key: API key
            context: Template context

        Returns:
            Headers from custom handler
        """
        if not self.auth_config.custom_handler:
            raise ServiceError("Custom handler not configured")

        secret = await self.resolve_secret(api_key)
        context["secret"] = secret

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "custom_auth", self.auth_config.custom_handler
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "get_auth_headers"):
                    import asyncio

                    handler = module.get_auth_headers
                    if asyncio.iscoroutinefunction(handler):
                        return await handler(api_key, context, self.auth_config)
                    else:
                        return handler(api_key, context, self.auth_config)
                else:
                    raise ServiceError("Custom handler missing get_auth_headers function")
        except Exception as e:
            logger.error(f"Failed to execute custom auth handler: {e}")
            raise ServiceError(f"Custom auth handler failed: {e}")

        return {}


class AuthStrategyFactory:
    """Factory for creating auth strategy instances."""

    @staticmethod
    def create(auth_config: AuthConfig, api_key_port: APIKeyPort | None = None) -> BaseAuthStrategy:
        """Create an auth strategy instance.

        Args:
            auth_config: Authentication configuration
            api_key_port: Port for resolving API keys

        Returns:
            Auth strategy instance
        """
        strategy_map = {
            AuthStrategy.NONE: NoAuthStrategy,
            AuthStrategy.API_KEY_HEADER: ApiKeyHeaderStrategy,
            AuthStrategy.API_KEY_QUERY: ApiKeyQueryStrategy,
            AuthStrategy.OAUTH2_BEARER: OAuth2BearerStrategy,
            AuthStrategy.BASIC: BasicAuthStrategy,
            AuthStrategy.OAUTH2_CLIENT_CREDENTIALS: OAuth2ClientCredentialsStrategy,
            AuthStrategy.CUSTOM: CustomAuthStrategy,
        }

        strategy_class = strategy_map.get(auth_config.strategy)
        if not strategy_class:
            raise ValueError(f"Unknown auth strategy: {auth_config.strategy}")

        return strategy_class(auth_config, api_key_port)
