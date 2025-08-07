"""GraphQL schema factory for DiPeO.

This module creates the complete GraphQL schema using the ServiceRegistry
for dependency injection, keeping the schema definition in the application layer
while the server remains a thin HTTP adapter.
"""

import strawberry
from strawberry.schema.config import StrawberryConfig

from dipeo.application.registry import ServiceRegistry

from .schema.queries import create_query_type
from .schema.mutation_factory import create_mutation_type
from .schema.subscriptions import create_subscription_type
from .types.scalars import JSONScalar

# Import generated types
# TODO: Fix dict[str, Any] field handling in generated types before enabling
# from dipeo.diagram_generated.graphql.strawberry_nodes import (
#     ApiJobDataType,
#     CodeJobDataType,
#     ConditionDataType,
#     DbDataType,
#     EndpointDataType,
#     HookDataType,
#     IntegratedApiDataType,
#     JsonSchemaValidatorDataType,
#     NotionDataType,
#     PersonBatchJobDataType,
#     PersonJobDataType,
#     StartDataType,
#     SubDiagramDataType,
#     TemplateJobDataType,
#     TypescriptAstDataType,
#     UserResponseDataType,
# )
# from dipeo.diagram_generated.graphql.node_mutations import NodeMutations


def create_schema(registry: ServiceRegistry) -> strawberry.Schema:
    """Create a complete GraphQL schema with injected service registry.
    
    Args:
        registry: The service registry containing all application services
        
    Returns:
        A Strawberry GraphQL schema ready to be served
    """
    # Import scalar types
    from .types.scalars import (
        NodeIDScalar,
        HandleIDScalar,
        ArrowIDScalar,
        PersonIDScalar,
        ApiKeyIDScalar,
        DiagramIDScalar,
        ExecutionIDScalar,
        HookIDScalar,
        TaskIDScalar,
    )
    
    # Create schema components with injected registry
    Query = create_query_type(registry)
    Mutation = create_mutation_type(registry)
    Subscription = create_subscription_type(registry)
    
    # Create the schema with configuration
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        extensions=[],
        # Disable auto camelCase conversion to keep snake_case field names
        config=StrawberryConfig(auto_camel_case=False),
        scalar_overrides={
            # Register JSON scalar type
            dict: JSONScalar
        },
        # Register all scalar types explicitly
        types=[
            NodeIDScalar,
            HandleIDScalar,
            ArrowIDScalar,
            PersonIDScalar,
            ApiKeyIDScalar,
            DiagramIDScalar,
            ExecutionIDScalar,
            HookIDScalar,
            TaskIDScalar,
        ],
        # Register concrete types for interface resolution
        # TODO: Enable when dict[str, Any] field handling is fixed in generated types
        # types=[
        #     ApiJobDataType,
        #     CodeJobDataType,
        #     ConditionDataType,
        #     DbDataType,
        #     EndpointDataType,
        #     HookDataType,
        #     IntegratedApiDataType,
        #     JsonSchemaValidatorDataType,
        #     NotionDataType,
        #     PersonBatchJobDataType,
        #     PersonJobDataType,
        #     StartDataType,
        #     SubDiagramDataType,
        #     TemplateJobDataType,
        #     TypescriptAstDataType,
        #     UserResponseDataType,
        # ]
    )
    
    return schema