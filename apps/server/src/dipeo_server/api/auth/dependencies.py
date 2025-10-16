"""FastAPI dependencies for MCP authentication.

Provides security dependencies for protecting MCP endpoints with OAuth 2.1.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dipeo.config.base_logger import get_module_logger

from .oauth import TokenData, get_oauth_config, verify_api_key, verify_jwt_token

logger = get_module_logger(__name__)

# HTTP Bearer token extractor
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[TokenData]:
    """Authenticate the current user via OAuth 2.1 or API key.

    This dependency enforces authentication based on configuration:
    - If MCP_AUTH_ENABLED=false: No authentication required
    - If MCP_AUTH_REQUIRED=false: Authentication is optional (validates if provided)
    - If MCP_AUTH_REQUIRED=true: Authentication is mandatory

    Supports two authentication methods:
    1. Bearer token (OAuth 2.1 JWT)
    2. API key (via X-API-Key header)

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (from Authorization header)

    Returns:
        TokenData if authenticated, None if optional auth and not provided

    Raises:
        HTTPException: If authentication is required but fails
    """
    config = get_oauth_config()

    # If authentication is disabled, allow access
    if not config.enabled:
        logger.debug("Authentication disabled, allowing access")
        return None

    # Try Bearer token authentication
    if credentials and credentials.credentials:
        token = credentials.credentials
        logger.debug("Attempting Bearer token authentication")

        if config.jwt_enabled:
            try:
                token_data = verify_jwt_token(token)
                logger.info(f"Authenticated user via JWT: {token_data.sub}")
                return token_data
            except HTTPException as e:
                if config.require_auth:
                    raise
                logger.debug(f"JWT verification failed: {e.detail}")

    # Try API key authentication
    api_key = request.headers.get("X-API-Key")
    if api_key:
        logger.debug("Attempting API key authentication")

        if config.api_key_enabled:
            if verify_api_key(api_key):
                logger.info("Authenticated via API key")
                return TokenData(sub="api_key_user")
            elif config.require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": 'Bearer realm="MCP Server"'},
                )

    # If no authentication provided and it's required
    if config.require_auth:
        logger.warning("Authentication required but not provided")

        # Build WWW-Authenticate header for OAuth discovery
        auth_header = 'Bearer realm="MCP Server"'

        if config.authorization_server_url:
            # Include OAuth server URL for MCP clients to discover
            auth_header += f', auth_server="{config.authorization_server_url}"'

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": auth_header},
        )

    # Optional authentication - no credentials provided
    logger.debug("Optional authentication, no credentials provided")
    return None


async def optional_authentication(
    user: Optional[TokenData] = Depends(get_current_user),
) -> Optional[TokenData]:
    """Optional authentication dependency.

    This is an alias for get_current_user that makes it explicit
    that authentication is optional for the endpoint.

    Args:
        user: Authenticated user (if provided)

    Returns:
        TokenData if authenticated, None otherwise
    """
    return user


async def require_authentication(
    user: Optional[TokenData] = Depends(get_current_user),
) -> TokenData:
    """Required authentication dependency.

    Forces authentication regardless of MCP_AUTH_REQUIRED setting.
    Use this for endpoints that always require authentication.

    Args:
        user: Authenticated user

    Returns:
        TokenData

    Raises:
        HTTPException: If not authenticated
    """
    if user is None:
        config = get_oauth_config()
        auth_header = 'Bearer realm="MCP Server"'
        if config.authorization_server_url:
            auth_header += f', auth_server="{config.authorization_server_url}"'

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
            headers={"WWW-Authenticate": auth_header},
        )

    return user
