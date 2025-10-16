"""Tests for FastAPI authentication dependencies.

These tests verify the authentication dependency behavior including:
- Optional authentication
- Required authentication
- Bearer token authentication
- API key authentication
"""

import os
import time
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
from fastapi import HTTPException, Request

from dipeo_server.api.auth.dependencies import (
    get_current_user,
    optional_authentication,
    require_authentication,
)
from dipeo_server.api.auth.oauth import TokenData


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.headers = {}
    return request


@pytest.fixture
def hs256_secret():
    """HS256 secret key for testing."""
    return "test-secret-key-for-hs256"


@pytest.fixture
def valid_jwt_token(hs256_secret):
    """Create a valid JWT token."""
    payload = {
        "sub": "test-user",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, hs256_secret, algorithm="HS256")


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_auth_disabled(self, mock_request):
        """Test that authentication is bypassed when disabled."""
        with patch.dict(os.environ, {"MCP_AUTH_ENABLED": "false"}, clear=True):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, None)
            assert user is None

    @pytest.mark.asyncio
    async def test_valid_jwt_token(self, mock_request, valid_jwt_token, hs256_secret):
        """Test authentication with valid JWT token."""
        # Create bearer credentials mock
        credentials = Mock()
        credentials.credentials = valid_jwt_token

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, credentials)
            assert user is not None
            assert user.sub == "test-user"
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_valid_api_key(self, mock_request):
        """Test authentication with valid API key."""
        test_api_key = "test-api-key-12345"
        mock_request.headers = {"X-API-Key": test_api_key}

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_API_KEY_ENABLED": "true",
                "MCP_API_KEYS": test_api_key,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, None)
            assert user is not None
            assert user.sub == "api_key_user"

    @pytest.mark.asyncio
    async def test_invalid_jwt_optional_auth(
        self, mock_request, hs256_secret
    ):
        """Test that invalid JWT is ignored when auth is optional."""
        credentials = Mock()
        credentials.credentials = "invalid.jwt.token"

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "false",  # Optional
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            # Should return None, not raise exception
            user = await get_current_user(mock_request, credentials)
            assert user is None

    @pytest.mark.asyncio
    async def test_invalid_jwt_required_auth(
        self, mock_request, hs256_secret
    ):
        """Test that invalid JWT raises exception when auth is required."""
        credentials = Mock()
        credentials.credentials = "invalid.jwt.token"

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "true",  # Required
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_optional_auth(self, mock_request):
        """Test that invalid API key is ignored when auth is optional."""
        mock_request.headers = {"X-API-Key": "invalid-key"}

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "false",  # Optional
                "MCP_API_KEY_ENABLED": "true",
                "MCP_API_KEYS": "valid-key",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, None)
            assert user is None

    @pytest.mark.asyncio
    async def test_invalid_api_key_required_auth(self, mock_request):
        """Test that invalid API key raises exception when auth is required."""
        mock_request.headers = {"X-API-Key": "invalid-key"}

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "true",  # Required
                "MCP_API_KEY_ENABLED": "true",
                "MCP_API_KEYS": "valid-key",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None)

            assert exc_info.value.status_code == 401
            assert "Invalid API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_credentials_optional_auth(self, mock_request):
        """Test that no credentials is accepted when auth is optional."""
        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "false",  # Optional
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, None)
            assert user is None

    @pytest.mark.asyncio
    async def test_no_credentials_required_auth(self, mock_request):
        """Test that no credentials raises exception when auth is required."""
        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "true",  # Required
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None)

            assert exc_info.value.status_code == 401
            assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_www_authenticate_header(self, mock_request):
        """Test that WWW-Authenticate header is included in 401 responses."""
        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_AUTH_REQUIRED": "true",
                "MCP_OAUTH_SERVER_URL": "https://auth.example.com",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None)

            assert exc_info.value.status_code == 401
            assert "WWW-Authenticate" in exc_info.value.headers
            assert "Bearer" in exc_info.value.headers["WWW-Authenticate"]
            assert (
                "auth.example.com" in exc_info.value.headers["WWW-Authenticate"]
            )

    @pytest.mark.asyncio
    async def test_jwt_takes_precedence_over_api_key(
        self, mock_request, valid_jwt_token, hs256_secret
    ):
        """Test that JWT authentication is tried before API key."""
        test_api_key = "test-api-key"
        mock_request.headers = {"X-API-Key": test_api_key}

        credentials = Mock()
        credentials.credentials = valid_jwt_token

        with patch.dict(
            os.environ,
            {
                "MCP_AUTH_ENABLED": "true",
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
                "MCP_API_KEY_ENABLED": "true",
                "MCP_API_KEYS": test_api_key,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            user = await get_current_user(mock_request, credentials)
            # Should authenticate via JWT, not API key
            assert user.sub == "test-user"
            assert user.sub != "api_key_user"


class TestOptionalAuthentication:
    """Test optional_authentication dependency."""

    @pytest.mark.asyncio
    async def test_optional_authentication_with_user(self):
        """Test optional authentication when user is authenticated."""
        mock_user = TokenData(sub="test-user")

        result = await optional_authentication(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_optional_authentication_without_user(self):
        """Test optional authentication when user is not authenticated."""
        result = await optional_authentication(None)
        assert result is None


class TestRequireAuthentication:
    """Test require_authentication dependency."""

    @pytest.mark.asyncio
    async def test_require_authentication_with_user(self):
        """Test required authentication when user is authenticated."""
        mock_user = TokenData(sub="test-user")

        result = await require_authentication(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_authentication_without_user(self):
        """Test required authentication when user is not authenticated."""
        with patch.dict(
            os.environ,
            {"MCP_OAUTH_SERVER_URL": "https://auth.example.com"},
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                await require_authentication(None)

            assert exc_info.value.status_code == 401
            assert "Authentication required" in exc_info.value.detail
            assert "WWW-Authenticate" in exc_info.value.headers
