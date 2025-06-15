"""GraphQL resolvers module."""
from .diagram_resolver import diagram_resolver
from .execution_resolver import execution_resolver
from .person_resolver import person_resolver

__all__ = ["diagram_resolver", "execution_resolver", "person_resolver"]