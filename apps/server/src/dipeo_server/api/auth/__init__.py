"""Authentication module for DiPeO MCP server.

Provides OAuth 2.1 authentication for MCP endpoints, supporting:
- JWT Bearer token validation (OAuth 2.1)
- API Key authentication (simple fallback)
- Optional authentication (can be disabled)
"""

from .dependencies import get_current_user, optional_authentication
from .oauth import MCPOAuthConfig, get_oauth_config

__all__ = [
    "get_current_user",
    "optional_authentication",
    "MCPOAuthConfig",
    "get_oauth_config",
]
