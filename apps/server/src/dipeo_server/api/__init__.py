"""API layer - FastAPI/GraphQL adapters."""

from .context import get_request_context, get_graphql_context
from .middleware import setup_middleware
from .router import setup_routes

__all__ = [
    "get_request_context",
    "get_graphql_context",  # Backward compatibility
    "setup_middleware",
    "setup_routes",
]
