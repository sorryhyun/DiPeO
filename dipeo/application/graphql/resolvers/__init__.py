"""GraphQL resolvers for DiPeO.

Resolvers use the ServiceRegistry to access application services,
keeping the GraphQL layer focused on API concerns while delegating
business logic to the appropriate services.

Note: DiagramResolver, ExecutionResolver, and PersonResolver have been
removed in favor of direct service access in query_resolvers.py.
Only ProviderResolver remains as it contains complex business logic.
"""

__all__: list[str] = []
