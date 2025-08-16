"""Tests for the Provider Registry and Manifest System."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import yaml
import json

from dipeo.infrastructure.services.integrated_api.registry import ProviderRegistry
from dipeo.infrastructure.services.integrated_api.generic_provider import GenericHTTPProvider
from dipeo.infrastructure.services.integrated_api.manifest_schema import (
    ProviderManifest,
    validate_manifest,
    create_example_manifest,
    AuthStrategy,
    RetryStrategy,
    RateLimitAlgorithm
)
from dipeo.infrastructure.services.integrated_api.auth_strategies import (
    AuthStrategyFactory,
    OAuth2BearerStrategy,
    ApiKeyHeaderStrategy,
    BasicAuthStrategy
)
from dipeo.infrastructure.services.integrated_api.rate_limiter import (
    RateLimiter,
    TokenBucket,
    SlidingWindow
)
from dipeo.infrastructure.services.integrated_api.providers.base_provider import BaseApiProvider


class MockProvider(BaseApiProvider):
    """Mock provider for testing."""
    
    def __init__(self):
        super().__init__("mock", ["operation1", "operation2"])
    
    async def _execute_operation(self, operation, config, resource_id, api_key, timeout):
        return {"success": True, "operation": operation}


@pytest.mark.asyncio
async def test_provider_registry_initialization():
    """Test that ProviderRegistry initializes correctly."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    assert registry._initialized is True
    assert len(registry.list_providers()) == 0


@pytest.mark.asyncio
async def test_provider_registration():
    """Test registering providers programmatically."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    # Register a mock provider
    mock_provider = MockProvider()
    await registry.register("mock", mock_provider, {"version": "1.0.0"})
    
    # Check provider is registered
    assert "mock" in registry.list_providers()
    assert registry.get_provider("mock") == mock_provider
    
    # Check metadata
    metadata = registry.get_provider_metadata("mock")
    assert metadata["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_provider_info():
    """Test getting provider information."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    mock_provider = MockProvider()
    await registry.register("mock", mock_provider)
    
    info = registry.get_provider_info("mock")
    assert info is not None
    assert info["name"] == "mock"
    assert info["operations"] == ["operation1", "operation2"]
    assert info["provider_type"] == "MockProvider"


@pytest.mark.asyncio
async def test_manifest_validation():
    """Test manifest schema validation."""
    # Create a valid manifest
    manifest_dict = create_example_manifest()
    manifest = validate_manifest(manifest_dict)
    
    assert isinstance(manifest, ProviderManifest)
    assert manifest.name == "example_api"
    assert manifest.version == "1.0.0"
    assert manifest.base_url == "https://api.example.com"
    
    # Check auth config
    assert manifest.auth.strategy == AuthStrategy.OAUTH2_BEARER
    assert manifest.auth.header == "Authorization"
    
    # Check operations
    assert "get_resource" in manifest.operations
    assert "create_resource" in manifest.operations
    
    get_op = manifest.operations["get_resource"]
    assert get_op.method == "GET"
    assert get_op.path == "/resources/{id}"


@pytest.mark.asyncio
async def test_load_manifest_from_file():
    """Test loading a manifest-based provider from file."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    # Create a temporary manifest file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        manifest_data = {
            "name": "test_api",
            "version": "1.0.0",
            "base_url": "https://test.example.com",
            "auth": {
                "strategy": "api_key_header",
                "header": "X-API-Key"
            },
            "operations": {
                "test_op": {
                    "method": "GET",
                    "path": "/test"
                }
            }
        }
        yaml.dump(manifest_data, f)
        manifest_path = Path(f.name)
    
    try:
        # Load the manifest
        await registry._load_single_manifest(manifest_path)
        
        # Check provider was registered
        assert "test_api" in registry.list_providers()
        
        # Check it's a GenericHTTPProvider
        provider = registry.get_provider("test_api")
        assert isinstance(provider, GenericHTTPProvider)
        assert provider.manifest.name == "test_api"
        assert "test_op" in provider.supported_operations
        
        # Check metadata
        metadata = registry.get_provider_metadata("test_api")
        assert metadata["type"] == "manifest"
        assert metadata["manifest_path"] == str(manifest_path)
        
    finally:
        # Cleanup
        manifest_path.unlink()


@pytest.mark.asyncio
async def test_auth_strategy_factory():
    """Test auth strategy creation."""
    from dipeo.infrastructure.services.integrated_api.manifest_schema import AuthConfig
    
    # OAuth2 Bearer
    auth_config = AuthConfig(
        strategy=AuthStrategy.OAUTH2_BEARER,
        header="Authorization",
        format="Bearer {{secret.token}}"
    )
    strategy = AuthStrategyFactory.create(auth_config)
    assert isinstance(strategy, OAuth2BearerStrategy)
    
    # API Key Header
    auth_config = AuthConfig(
        strategy=AuthStrategy.API_KEY_HEADER,
        header="X-API-Key"
    )
    strategy = AuthStrategyFactory.create(auth_config)
    assert isinstance(strategy, ApiKeyHeaderStrategy)
    
    # Basic Auth
    auth_config = AuthConfig(
        strategy=AuthStrategy.BASIC,
        header="Authorization"
    )
    strategy = AuthStrategyFactory.create(auth_config)
    assert isinstance(strategy, BasicAuthStrategy)


@pytest.mark.asyncio
async def test_auth_strategy_headers():
    """Test auth strategy header generation."""
    from dipeo.infrastructure.services.integrated_api.manifest_schema import AuthConfig
    
    # OAuth2 Bearer
    auth_config = AuthConfig(
        strategy=AuthStrategy.OAUTH2_BEARER,
        header="Authorization",
        format="Bearer {{secret.token}}"
    )
    strategy = AuthStrategyFactory.create(auth_config)
    
    context = {}
    headers = await strategy.get_auth_headers("test-token", context)
    
    assert "Authorization" in headers
    # The header value depends on secret resolution
    assert headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
async def test_rate_limiter_token_bucket():
    """Test token bucket rate limiting."""
    from dipeo.infrastructure.services.integrated_api.manifest_schema import RateLimitConfig
    
    config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        capacity=2,
        refill_per_sec=1.0
    )
    
    limiter = RateLimiter(config)
    
    # Should allow first two requests immediately
    assert limiter.can_proceed() is True
    await limiter.acquire()
    
    assert limiter.can_proceed() is True
    await limiter.acquire()
    
    # Third request should require waiting
    assert limiter.can_proceed() is False


@pytest.mark.asyncio
async def test_generic_provider_initialization():
    """Test GenericHTTPProvider initialization."""
    manifest_dict = {
        "name": "test_provider",
        "version": "1.0.0",
        "base_url": "https://api.test.com",
        "auth": {
            "strategy": "api_key_header",
            "header": "X-API-Key"
        },
        "operations": {
            "get_item": {
                "method": "GET",
                "path": "/items/{{config.item_id}}",
                "response": {
                    "success_codes": [200],
                    "json_pointer": "$.data"
                }
            }
        }
    }
    
    provider = GenericHTTPProvider(manifest_dict)
    await provider.initialize()
    
    assert provider.provider_name == "test_provider"
    assert "get_item" in provider.supported_operations
    assert provider.auth_strategy is not None
    
    # Test URL building
    context = {"config": {"item_id": "123"}}
    url = provider._build_url("/items/{{config.item_id}}", context)
    assert url == "https://api.test.com/items/123"


@pytest.mark.asyncio
async def test_provider_statistics():
    """Test provider registry statistics."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    # Register some providers
    mock1 = MockProvider()
    mock2 = MockProvider()
    await registry.register("mock1", mock1, {"type": "programmatic"})
    await registry.register("mock2", mock2, {"type": "programmatic"})
    
    stats = registry.get_statistics()
    
    assert stats["total_providers"] == 2
    assert stats["total_operations"] == 4  # 2 operations per provider
    assert stats["provider_types"]["programmatic"] == 2
    assert len(stats["providers"]) == 2


@pytest.mark.asyncio
async def test_provider_removal():
    """Test removing a provider from registry."""
    registry = ProviderRegistry()
    await registry.initialize()
    
    mock_provider = MockProvider()
    await registry.register("mock", mock_provider)
    
    assert "mock" in registry.list_providers()
    
    # Remove the provider
    result = await registry.remove_provider("mock")
    assert result is True
    assert "mock" not in registry.list_providers()
    
    # Try to remove non-existent provider
    result = await registry.remove_provider("nonexistent")
    assert result is False


def test_manifest_schema_enums():
    """Test that manifest schema enums have expected values."""
    assert AuthStrategy.OAUTH2_BEARER.value == "oauth2_bearer"
    assert AuthStrategy.API_KEY_HEADER.value == "api_key_header"
    assert AuthStrategy.BASIC.value == "basic"
    
    assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
    assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"
    
    assert RateLimitAlgorithm.TOKEN_BUCKET.value == "token_bucket"
    assert RateLimitAlgorithm.SLIDING_WINDOW.value == "sliding_window"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])