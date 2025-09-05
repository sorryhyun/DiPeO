"""GraphQL schema factory for DiPeO.

This module creates the complete GraphQL schema using the ServiceRegistry
for dependency injection, keeping the schema definition in the application layer
while the server remains a thin HTTP adapter.
"""

import strawberry
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

from dipeo.application.registry import ServiceRegistry

from .schema.mutation_factory import create_mutation_type
from .schema.queries import create_query_type
from .schema.subscriptions import create_subscription_type

# Import generated types
# TODO: Fix Dict field handling in generated types
# from dipeo.diagram_generated.graphql.strawberry_nodes import (
#     ApiJobDataType,
#     CodeJobDataType,
#     ConditionDataType,
#     DBDataType,
#     EndpointDataType,
#     HookDataType,
#     IntegratedApiDataType,
#     JsonSchemaValidatorDataType,
#     PersonBatchJobDataType,
#     PersonJobDataType,
#     StartDataType,
#     SubDiagramDataType,
#     TemplateJobDataType,
#     TypescriptAstDataType,
#     UserResponseDataType,
# )
# Note: strawberry_domain.py needs to be regenerated
# from dipeo.diagram_generated.graphql.strawberry_domain import (
#     MemorySettingsType,
#     ToolConfigType,
# )


def create_schema(registry: ServiceRegistry) -> strawberry.Schema:
    """Create a complete GraphQL schema with injected service registry.

    Args:
        registry: The service registry containing all application services

    Returns:
        A Strawberry GraphQL schema ready to be served
    """
    # Import scalar types
    from .types.scalars import (
        ApiKeyIDScalar,
        ArrowIDScalar,
        DiagramIDScalar,
        ExecutionIDScalar,
        HandleIDScalar,
        HookIDScalar,
        NodeIDScalar,
        PersonIDScalar,
        TaskIDScalar,
    )

    # Create schema components with injected registry
    query = create_query_type(registry)
    mutation = create_mutation_type(registry)
    subscription = create_subscription_type(registry)

    # Create the schema with configuration
    schema = strawberry.Schema(
        query=query,
        mutation=mutation,
        subscription=subscription,
        extensions=[],
        # Disable auto camelCase conversion to keep snake_case field names
        config=StrawberryConfig(auto_camel_case=False),
        scalar_overrides={
            # Register JSON scalar type
            dict: JSON
        },
        # Register all scalar and generated types
        types=[
            # Scalar types
            NodeIDScalar,
            HandleIDScalar,
            ArrowIDScalar,
            PersonIDScalar,
            ApiKeyIDScalar,
            DiagramIDScalar,
            ExecutionIDScalar,
            HookIDScalar,
            TaskIDScalar,
            # Generated node data types
            # TODO: Fix Dict field handling before enabling
            # ApiJobDataType,
            # CodeJobDataType,
            # ConditionDataType,
            # DBDataType,
            # EndpointDataType,
            # HookDataType,
            # IntegratedApiDataType,
            # JsonSchemaValidatorDataType,
            # PersonBatchJobDataType,
            # PersonJobDataType,
            # StartDataType,
            # SubDiagramDataType,
            # TemplateJobDataType,
            # TypescriptAstDataType,
            # UserResponseDataType,
            # Domain types (need to be regenerated)
            # MemorySettingsType,
            # ToolConfigType,
        ],
    )

    return schema
