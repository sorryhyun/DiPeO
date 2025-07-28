"""GraphQL schema factory for DiPeO.

This module creates the complete GraphQL schema using the UnifiedServiceRegistry
for dependency injection, keeping the schema definition in the application layer
while the server remains a thin HTTP adapter.
"""

import strawberry
from strawberry.schema.config import StrawberryConfig

from dipeo.application.unified_service_registry import UnifiedServiceRegistry

from .schema.queries import create_query_type
from .schema.mutation_factory import create_mutation_type
from .schema.subscriptions import create_subscription_type
from .types.scalars import JSONScalar

# Import generated types
# TODO: Fix import issues before enabling
# from dipeo.diagram_generated.graphql.strawberry_nodes import (
#     ApiJobNodeDataType,
#     CodeJobNodeDataType,
#     ConditionNodeDataType,
#     DbNodeDataType,
#     EndpointNodeDataType,
#     HookNodeDataType,
#     JsonSchemaValidatorNodeDataType,
#     NotionNodeDataType,
#     PersonBatchJobNodeDataType,
#     PersonJobNodeDataType,
#     StartNodeDataType,
#     SubDiagramNodeDataType,
#     TemplateJobNodeDataType,
#     TypescriptAstNodeDataType,
#     UserResponseNodeDataType,
# )
# from dipeo.diagram_generated.graphql.node_mutations import NodeMutations


def create_schema(registry: UnifiedServiceRegistry) -> strawberry.Schema:
    """Create a complete GraphQL schema with injected service registry.
    
    Args:
        registry: The unified service registry containing all application services
        
    Returns:
        A Strawberry GraphQL schema ready to be served
    """
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
        # Register concrete types for interface resolution
        # TODO: Enable when import issues are fixed
        # types=[
        #     ApiJobNodeDataType,
        #     CodeJobNodeDataType,
        #     ConditionNodeDataType,
        #     DbNodeDataType,
        #     EndpointNodeDataType,
        #     HookNodeDataType,
        #     JsonSchemaValidatorNodeDataType,
        #     NotionNodeDataType,
        #     PersonBatchJobNodeDataType,
        #     PersonJobNodeDataType,
        #     StartNodeDataType,
        #     SubDiagramNodeDataType,
        #     TemplateJobNodeDataType,
        #     TypescriptAstNodeDataType,
        #     UserResponseNodeDataType,
        # ]
    )
    
    return schema