"""GraphQL schema factory for DiPeO.

This module creates the complete GraphQL schema using the ServiceRegistry
for dependency injection, keeping the schema definition in the application layer
while the server remains a thin HTTP adapter.
"""

import strawberry
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

from dipeo.application.registry import ServiceRegistry

# Import generated schema (Now includes fixed Subscription)
from dipeo.diagram_generated.graphql.generated_schema import Mutation, Query, Subscription


def create_schema(registry: ServiceRegistry) -> strawberry.Schema:
    """Create a complete GraphQL schema with injected service registry.

    Args:
        registry: The service registry containing all application services

    Returns:
        A Strawberry GraphQL schema ready to be served
    """
    # Import scalar types from generated code
    # Import provider types for registration
    from dipeo.application.graphql.graphql_types.provider_types import (
        AuthConfigType,
        IntegrationTestResultType,
        OperationSchemaType,
        OperationType,
        ProviderMetadataType,
        ProviderStatisticsType,
        ProviderType,
        RateLimitConfigType,
        RetryPolicyType,
    )
    from dipeo.diagram_generated.graphql.scalars import (
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

    # Use generated schema for Query, Mutation, and Subscription
    query = Query
    mutation = Mutation
    subscription = Subscription

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
        # Register only custom scalar types that Strawberry can't auto-discover
        # Domain types referenced by Query/Mutation/Subscription fields are auto-discovered
        types=[
            # Custom scalar types (required for GraphQL schema)
            NodeIDScalar,
            HandleIDScalar,
            ArrowIDScalar,
            PersonIDScalar,
            ApiKeyIDScalar,
            DiagramIDScalar,
            ExecutionIDScalar,
            HookIDScalar,
            TaskIDScalar,
            # Provider types (manually defined, not generated)
            ProviderType,
            OperationType,
            ProviderMetadataType,
            AuthConfigType,
            RateLimitConfigType,
            RetryPolicyType,
            OperationSchemaType,
            ProviderStatisticsType,
            IntegrationTestResultType,
        ],
    )

    return schema
