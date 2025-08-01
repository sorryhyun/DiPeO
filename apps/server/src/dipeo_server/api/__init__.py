"""API layer - FastAPI/GraphQL adapters."""

from .context import get_graphql_context, get_request_context
from .middleware import setup_middleware
from .router import setup_routes

__all__ = [
    "get_graphql_context",  # Backward compatibility
    "get_request_context",
    "setup_middleware",
    "setup_routes",
]
