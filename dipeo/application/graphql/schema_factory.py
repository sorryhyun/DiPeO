"""GraphQL schema factory for DiPeO.

This module creates the complete GraphQL schema using the ServiceRegistry
for dependency injection, keeping the schema definition in the application layer
while the server remains a thin HTTP adapter.
"""

import strawberry
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

from dipeo.application.registry import ServiceRegistry
from dipeo.diagram_generated.graphql.generated_schema import Mutation, Query, Subscription


def create_schema(registry: ServiceRegistry) -> strawberry.Schema:
    """Create a complete GraphQL schema with injected service registry.

    Args:
        registry: The service registry containing all application services

    Returns:
        A Strawberry GraphQL schema ready to be served
    """
    from dipeo.diagram_generated.graphql.domain_types import (
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

    query = Query
    mutation = Mutation
    subscription = Subscription

    schema = strawberry.Schema(
        query=query,
        mutation=mutation,
        subscription=subscription,
        extensions=[],
        config=StrawberryConfig(auto_camel_case=False),
        scalar_overrides={dict: JSON},
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
