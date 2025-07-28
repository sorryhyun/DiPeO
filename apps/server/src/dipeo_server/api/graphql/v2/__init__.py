"""GraphQL v2 schema with interface-based design."""

from .schema import schema_v2, create_v2_graphql_router
from .types import Node, PersonNode, CodeNode, StartNode

__all__ = [
    "schema_v2",
    "create_v2_graphql_router",
    "Node",
    "PersonNode", 
    "CodeNode",
    "StartNode",
]