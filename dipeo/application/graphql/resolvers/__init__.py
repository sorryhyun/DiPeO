"""GraphQL resolvers for DiPeO.

Resolvers use the ServiceRegistry to access application services,
keeping the GraphQL layer focused on API concerns while delegating
business logic to the appropriate services.
"""

from .diagram import DiagramResolver
from .execution import ExecutionResolver
from .person import PersonResolver

__all__ = ["DiagramResolver", "ExecutionResolver", "PersonResolver"]