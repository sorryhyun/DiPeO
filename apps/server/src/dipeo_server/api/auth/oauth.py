"""OAuth 2.1 configuration and token validation for MCP server.

This module implements OAuth 2.1 Resource Server pattern as required by
the MCP specification (2025-03-26).
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class TokenData(BaseModel):
    """Validated token data."""

    sub: str  # Subject (user ID)
    iss: Optional[str] = None  # Issuer
    aud: Optional[str] = None  # Audience
    exp: Optional[int] = None  # Expiration
    scope: Optional[str] = None  # OAuth scopes
    email: Optional[str] = None  # User email (if available)


@dataclass
class MCPOAuthConfig:
    """OAuth 2.1 configuration for MCP server."""

    # Authentication mode
    enabled: bool = True
    require_auth: bool = False  # If False, authentication is optional

    # API Key authentication (simple fallback)
    api_key_enabled: bool = True
    api_keys: set[str] = None  # Valid API keys

    # OAuth 2.1 JWT validation
    jwt_enabled: bool = True
    jwt_algorithm: str = "RS256"  # Default for OAuth 2.1
    jwt_secret: Optional[str] = None  # For HS256 (symmetric)
    jwt_public_key: Optional[str] = None  # For RS256 (asymmetric)
    jwt_audience: Optional[str] = None  # Expected audience
    jwt_issuer: Optional[str] = None  # Expected issuer

    # OAuth Authorization Server metadata
    authorization_server_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    registration_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.api_keys is None:
            self.api_keys = set()

    @classmethod
    def from_env(cls) -> "MCPOAuthConfig":
        """Create OAuth config from environment variables.

        Environment Variables:
            MCP_AUTH_ENABLED: Enable/disable authentication (default: true)
            MCP_AUTH_REQUIRED: Require authentication (default: false)

            MCP_API_KEY_ENABLED: Enable API key auth (default: true)
            MCP_API_KEYS: Comma-separated list of valid API keys

            MCP_JWT_ENABLED: Enable JWT validation (default: true)
            MCP_JWT_ALGORITHM: JWT algorithm (default: RS256)
            MCP_JWT_SECRET: Secret for HS256 algorithm
            MCP_JWT_PUBLIC_KEY: Public key for RS256 algorithm
            MCP_JWT_AUDIENCE: Expected audience claim
            MCP_JWT_ISSUER: Expected issuer claim

            MCP_OAUTH_SERVER_URL: OAuth authorization server base URL
            MCP_OAUTH_AUTHORIZATION_ENDPOINT: Authorization endpoint
            MCP_OAUTH_TOKEN_ENDPOINT: Token endpoint
            MCP_OAUTH_REGISTRATION_ENDPOINT: Client registration endpoint
            MCP_OAUTH_JWKS_URI: JWKS endpoint for key discovery

        Returns:
            MCPOAuthConfig instance
        """
        # Parse API keys
        api_keys_str = os.getenv("MCP_API_KEYS", "")
        api_keys = {key.strip() for key in api_keys_str.split(",") if key.strip()}

        # Read JWT public key from file if specified
        jwt_public_key = os.getenv("MCP_JWT_PUBLIC_KEY")
        jwt_public_key_file = os.getenv("MCP_JWT_PUBLIC_KEY_FILE")
        if jwt_public_key_file and os.path.exists(jwt_public_key_file):
            with open(jwt_public_key_file, "r") as f:
                jwt_public_key = f.read()

        return cls(
            enabled=os.getenv("MCP_AUTH_ENABLED", "true").lower() == "true",
            require_auth=os.getenv("MCP_AUTH_REQUIRED", "false").lower() == "true",
            api_key_enabled=os.getenv("MCP_API_KEY_ENABLED", "true").lower() == "true",
            api_keys=api_keys,
            jwt_enabled=os.getenv("MCP_JWT_ENABLED", "true").lower() == "true",
            jwt_algorithm=os.getenv("MCP_JWT_ALGORITHM", "RS256"),
            jwt_secret=os.getenv("MCP_JWT_SECRET"),
            jwt_public_key=jwt_public_key,
            jwt_audience=os.getenv("MCP_JWT_AUDIENCE"),
            jwt_issuer=os.getenv("MCP_JWT_ISSUER"),
            authorization_server_url=os.getenv("MCP_OAUTH_SERVER_URL"),
            authorization_endpoint=os.getenv("MCP_OAUTH_AUTHORIZATION_ENDPOINT"),
            token_endpoint=os.getenv("MCP_OAUTH_TOKEN_ENDPOINT"),
            registration_endpoint=os.getenv("MCP_OAUTH_REGISTRATION_ENDPOINT"),
            jwks_uri=os.getenv("MCP_OAUTH_JWKS_URI"),
        )


# Global OAuth config instance
_oauth_config: Optional[MCPOAuthConfig] = None


def get_oauth_config() -> MCPOAuthConfig:
    """Get the global OAuth configuration.

    Returns:
        MCPOAuthConfig instance
    """
    global _oauth_config
    if _oauth_config is None:
        _oauth_config = MCPOAuthConfig.from_env()
        logger.info(
            f"OAuth config loaded: enabled={_oauth_config.enabled}, "
            f"required={_oauth_config.require_auth}, "
            f"api_key={_oauth_config.api_key_enabled}, "
            f"jwt={_oauth_config.jwt_enabled}"
        )
    return _oauth_config


def verify_api_key(api_key: str) -> bool:
    """Verify an API key.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    config = get_oauth_config()

    if not config.api_key_enabled:
        return False

    if not config.api_keys:
        logger.warning("No API keys configured, but API key auth is enabled")
        return False

    return api_key in config.api_keys


def verify_jwt_token(token: str) -> TokenData:
    """Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        TokenData with validated claims

    Raises:
        HTTPException: If token is invalid
    """
    config = get_oauth_config()

    if not config.jwt_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication is not enabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Determine verification key
        if config.jwt_algorithm.startswith("HS"):
            # Symmetric key (HS256, HS384, HS512)
            if not config.jwt_secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT secret not configured for symmetric algorithm",
                )
            verify_key = config.jwt_secret
        elif config.jwt_algorithm.startswith("RS") or config.jwt_algorithm.startswith("ES"):
            # Asymmetric key (RS256, RS384, RS512, ES256, etc.)
            if not config.jwt_public_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT public key not configured for asymmetric algorithm",
                )
            verify_key = config.jwt_public_key
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported JWT algorithm: {config.jwt_algorithm}",
            )

        # Build verification options
        verify_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": config.jwt_audience is not None,
            "verify_iss": config.jwt_issuer is not None,
        }

        # Decode and verify token
        payload = jwt.decode(
            token,
            verify_key,
            algorithms=[config.jwt_algorithm],
            audience=config.jwt_audience,
            issuer=config.jwt_issuer,
            options=verify_options,
        )

        # Extract token data
        return TokenData(
            sub=payload.get("sub"),
            iss=payload.get("iss"),
            aud=payload.get("aud"),
            exp=payload.get("exp"),
            scope=payload.get("scope"),
            email=payload.get("email"),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error verifying JWT token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying token",
        )


def get_authorization_server_metadata() -> dict[str, Any]:
    """Get OAuth 2.0 Authorization Server Metadata (RFC 8414).

    This endpoint is required by MCP specification for metadata discovery.

    Returns:
        Authorization server metadata
    """
    config = get_oauth_config()

    if not config.authorization_server_url:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth authorization server not configured",
        )

    # Build metadata response
    metadata = {
        "issuer": config.jwt_issuer or config.authorization_server_url,
        "authorization_endpoint": config.authorization_endpoint
        or f"{config.authorization_server_url}/authorize",
        "token_endpoint": config.token_endpoint or f"{config.authorization_server_url}/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "code_challenge_methods_supported": ["S256"],  # PKCE required
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none",  # For public clients with PKCE
        ],
    }

    # Add optional fields if configured
    if config.registration_endpoint:
        metadata["registration_endpoint"] = config.registration_endpoint
    elif config.authorization_server_url:
        metadata["registration_endpoint"] = f"{config.authorization_server_url}/register"

    if config.jwks_uri:
        metadata["jwks_uri"] = config.jwks_uri

    return metadata
