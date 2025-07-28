"""GraphQL schema definitions for DiPeO application layer.

This package contains the GraphQL schema, queries, mutations, and resolvers
that define the API surface of DiPeO. By keeping these in the application
layer, we ensure the server is just a thin HTTP adapter.
"""

from .schema_factory import create_schema

__all__ = ["create_schema"]