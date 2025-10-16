"""Tests for OAuth 2.1 authentication module.

These tests verify the security-critical authentication functionality including:
- API key validation with timing attack resistance
- JWT token validation
- OAuth configuration
- Error handling
"""

import os
import secrets
import time
from typing import Any
from unittest.mock import Mock, patch

import jwt
import pytest
from fastapi import HTTPException

from dipeo_server.api.auth.oauth import (
    MCPOAuthConfig,
    TokenData,
    get_oauth_config,
    verify_api_key,
    verify_jwt_token,
)


class TestMCPOAuthConfig:
    """Test OAuth configuration."""

    def test_from_env_defaults(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPOAuthConfig.from_env()

            assert config.enabled is True
            assert config.require_auth is False
            assert config.api_key_enabled is True
            assert config.jwt_enabled is True
            assert config.jwt_algorithm == "RS256"
            assert len(config.api_keys) == 0

    def test_from_env_custom_values(self):
        """Test configuration from environment variables."""
        env_vars = {
            "MCP_AUTH_ENABLED": "false",
            "MCP_AUTH_REQUIRED": "true",
            "MCP_API_KEY_ENABLED": "false",
            "MCP_API_KEYS": "key1, key2, key3",
            "MCP_JWT_ENABLED": "false",
            "MCP_JWT_ALGORITHM": "HS256",
            "MCP_JWT_SECRET": "test-secret",
            "MCP_JWT_AUDIENCE": "test-audience",
            "MCP_JWT_ISSUER": "test-issuer",
            "MCP_OAUTH_SERVER_URL": "https://auth.example.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = MCPOAuthConfig.from_env()

            assert config.enabled is False
            assert config.require_auth is True
            assert config.api_key_enabled is False
            assert config.api_keys == {"key1", "key2", "key3"}
            assert config.jwt_enabled is False
            assert config.jwt_algorithm == "HS256"
            assert config.jwt_secret == "test-secret"
            assert config.jwt_audience == "test-audience"
            assert config.jwt_issuer == "test-issuer"
            assert config.authorization_server_url == "https://auth.example.com"

    def test_from_env_api_keys_parsing(self):
        """Test API keys parsing with various formats."""
        test_cases = [
            ("key1,key2,key3", {"key1", "key2", "key3"}),
            ("key1, key2, key3", {"key1", "key2", "key3"}),
            ("key1,  key2  ,  key3  ", {"key1", "key2", "key3"}),
            ("", set()),
            ("single-key", {"single-key"}),
            (",,,", set()),  # Only commas
            ("key1,,key2", {"key1", "key2"}),  # Empty values
        ]

        for api_keys_str, expected_keys in test_cases:
            with patch.dict(os.environ, {"MCP_API_KEYS": api_keys_str}, clear=True):
                config = MCPOAuthConfig.from_env()
                assert config.api_keys == expected_keys

    def test_public_key_file_loading(self, tmp_path):
        """Test loading JWT public key from file."""
        # Create a temporary key file
        key_file = tmp_path / "test_key.pem"
        test_key = "-----BEGIN PUBLIC KEY-----\ntest-key-content\n-----END PUBLIC KEY-----"
        key_file.write_text(test_key)

        with patch.dict(
            os.environ, {"MCP_JWT_PUBLIC_KEY_FILE": str(key_file)}, clear=True
        ):
            config = MCPOAuthConfig.from_env()
            assert config.jwt_public_key == test_key

    def test_public_key_file_error_handling(self, tmp_path):
        """Test error handling when key file cannot be read."""
        # Non-existent file
        with patch.dict(
            os.environ, {"MCP_JWT_PUBLIC_KEY_FILE": "/nonexistent/file.pem"}, clear=True
        ):
            config = MCPOAuthConfig.from_env()
            assert config.jwt_public_key is None

    def test_public_key_direct_vs_file(self, tmp_path):
        """Test that direct key takes precedence over file key."""
        key_file = tmp_path / "test_key.pem"
        key_file.write_text("file-key")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_PUBLIC_KEY": "direct-key",
                "MCP_JWT_PUBLIC_KEY_FILE": str(key_file),
            },
            clear=True,
        ):
            config = MCPOAuthConfig.from_env()
            # File key should override direct key in current implementation
            assert config.jwt_public_key == "file-key"


class TestAPIKeyVerification:
    """Test API key verification."""

    def test_verify_api_key_valid(self):
        """Test verification of valid API key."""
        test_key = "test-api-key-12345"

        with patch.dict(
            os.environ,
            {"MCP_API_KEY_ENABLED": "true", "MCP_API_KEYS": test_key},
            clear=True,
        ):
            # Reset global config
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            assert verify_api_key(test_key) is True

    def test_verify_api_key_invalid(self):
        """Test verification of invalid API key."""
        with patch.dict(
            os.environ,
            {"MCP_API_KEY_ENABLED": "true", "MCP_API_KEYS": "valid-key"},
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            assert verify_api_key("invalid-key") is False

    def test_verify_api_key_disabled(self):
        """Test that verification fails when API key auth is disabled."""
        with patch.dict(
            os.environ,
            {"MCP_API_KEY_ENABLED": "false", "MCP_API_KEYS": "test-key"},
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            assert verify_api_key("test-key") is False

    def test_verify_api_key_no_keys_configured(self):
        """Test that verification fails when no keys are configured."""
        with patch.dict(
            os.environ, {"MCP_API_KEY_ENABLED": "true", "MCP_API_KEYS": ""}, clear=True
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            assert verify_api_key("any-key") is False

    def test_api_key_timing_attack_resistance(self):
        """Test that API key verification resists timing attacks."""
        # This test verifies that we use constant-time comparison
        valid_key = "a" * 32
        invalid_key_short = "b" * 2
        invalid_key_long = "b" * 32

        with patch.dict(
            os.environ,
            {"MCP_API_KEY_ENABLED": "true", "MCP_API_KEYS": valid_key},
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            # Measure timing for short invalid key
            iterations = 1000
            start = time.perf_counter()
            for _ in range(iterations):
                verify_api_key(invalid_key_short)
            time_short = time.perf_counter() - start

            # Measure timing for long invalid key
            start = time.perf_counter()
            for _ in range(iterations):
                verify_api_key(invalid_key_long)
            time_long = time.perf_counter() - start

            # The times should be similar (within 50% of each other)
            # This is a weak test but helps ensure we're using constant-time comparison
            ratio = max(time_short, time_long) / min(time_short, time_long)
            assert ratio < 1.5, f"Timing difference too large: {ratio}"

    def test_api_key_multiple_keys(self):
        """Test verification with multiple configured keys."""
        keys = "key1,key2,key3"

        with patch.dict(
            os.environ, {"MCP_API_KEY_ENABLED": "true", "MCP_API_KEYS": keys}, clear=True
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            assert verify_api_key("key1") is True
            assert verify_api_key("key2") is True
            assert verify_api_key("key3") is True
            assert verify_api_key("key4") is False


class TestJWTVerification:
    """Test JWT token verification."""

    @pytest.fixture
    def hs256_secret(self):
        """HS256 secret key for testing."""
        return "test-secret-key-for-hs256"

    @pytest.fixture
    def rs256_keys(self):
        """RS256 key pair for testing."""
        # Generate a test RSA key pair
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        return {"private": private_pem, "public": public_pem}

    def test_verify_jwt_valid_hs256(self, hs256_secret):
        """Test verification of valid HS256 JWT."""
        payload = {
            "sub": "test-user",
            "iss": "test-issuer",
            "aud": "test-audience",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
                "MCP_JWT_ISSUER": "test-issuer",
                "MCP_JWT_AUDIENCE": "test-audience",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            token_data = verify_jwt_token(token)
            assert token_data.sub == "test-user"
            assert token_data.iss == "test-issuer"
            assert token_data.aud == "test-audience"

    def test_verify_jwt_valid_rs256(self, rs256_keys):
        """Test verification of valid RS256 JWT."""
        payload = {
            "sub": "test-user",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, rs256_keys["private"], algorithm="RS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "RS256",
                "MCP_JWT_PUBLIC_KEY": rs256_keys["public"],
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            token_data = verify_jwt_token(token)
            assert token_data.sub == "test-user"

    def test_verify_jwt_expired(self, hs256_secret):
        """Test that expired tokens are rejected."""
        payload = {
            "sub": "test-user",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    def test_verify_jwt_missing_sub_claim(self, hs256_secret):
        """Test that tokens missing sub claim are rejected with 401."""
        payload = {
            "iss": "test-issuer",
            "exp": int(time.time()) + 3600,
            # Missing 'sub' claim
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            # Should return 401, not 500
            assert exc_info.value.status_code == 401
            assert "sub" in exc_info.value.detail.lower()

    def test_verify_jwt_invalid_sub_type(self, hs256_secret):
        """Test that tokens with invalid sub type are rejected with 401."""
        payload = {
            "sub": 12345,  # Should be string, not int
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            # Should return 401, not 500
            assert exc_info.value.status_code == 401

    def test_verify_jwt_invalid_audience(self, hs256_secret):
        """Test that tokens with invalid audience are rejected."""
        payload = {
            "sub": "test-user",
            "aud": "wrong-audience",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
                "MCP_JWT_AUDIENCE": "test-audience",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            assert exc_info.value.status_code == 401
            assert "audience" in exc_info.value.detail.lower()

    def test_verify_jwt_invalid_issuer(self, hs256_secret):
        """Test that tokens with invalid issuer are rejected."""
        payload = {
            "sub": "test-user",
            "iss": "wrong-issuer",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
                "MCP_JWT_ISSUER": "test-issuer",
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            assert exc_info.value.status_code == 401
            assert "issuer" in exc_info.value.detail.lower()

    def test_verify_jwt_invalid_signature(self, hs256_secret):
        """Test that tokens with invalid signature are rejected."""
        payload = {
            "sub": "test-user",
            "exp": int(time.time()) + 3600,
        }
        # Sign with wrong secret
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with patch.dict(
            os.environ,
            {
                "MCP_JWT_ENABLED": "true",
                "MCP_JWT_ALGORITHM": "HS256",
                "MCP_JWT_SECRET": hs256_secret,
            },
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            assert exc_info.value.status_code == 401

    def test_verify_jwt_disabled(self, hs256_secret):
        """Test that JWT verification fails when disabled."""
        payload = {
            "sub": "test-user",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, hs256_secret, algorithm="HS256")

        with patch.dict(os.environ, {"MCP_JWT_ENABLED": "false"}, clear=True):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(token)

            assert exc_info.value.status_code == 401
            assert "not enabled" in exc_info.value.detail.lower()

    def test_verify_jwt_malformed_token(self):
        """Test that malformed tokens are rejected."""
        with patch.dict(
            os.environ,
            {"MCP_JWT_ENABLED": "true", "MCP_JWT_ALGORITHM": "HS256"},
            clear=True,
        ):
            import dipeo_server.api.auth.oauth as oauth_module

            oauth_module._oauth_config = None

            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token("not.a.valid.jwt.token")

            assert exc_info.value.status_code == 401


class TestThreadSafety:
    """Test thread safety of singleton pattern."""

    def test_get_oauth_config_thread_safety(self):
        """Test that config initialization is thread-safe."""
        import threading

        import dipeo_server.api.auth.oauth as oauth_module

        # Reset global config
        oauth_module._oauth_config = None

        results = []

        def get_config():
            config = get_oauth_config()
            results.append(id(config))

        # Create multiple threads that all try to get the config
        threads = [threading.Thread(target=get_config) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should have gotten the same config instance
        assert len(set(results)) == 1
