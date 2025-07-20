"""GraphQL queries for Diagram - Auto-generated."""

import strawberry
from typing import Optional

from dipeo_server.api.graphql.context import GraphQLContext
from dipeo_server.api.graphql.generated.types import (
    DiagramID,
    DiagramType,
    DiagramFilterInput,
    JSONScalar,
)


@strawberry.field
async def diagram(
    self,
    id: DiagramID,
    info: strawberry.Info[GraphQLContext]
) -> DiagramType | None:
    """Get a single Diagram by ID."""
    context: GraphQLContext = info.context
    service = context.get_service("diagram_service")
    
    entity = await service.get(id)
    
    if not entity:
        raise ValueError(f"Diagram with ID {id} not found")
    
    return entity

@strawberry.field
async def Diagrams(
    self,
    info: strawberry.Info[GraphQLContext],
    filter: DiagramFilterInput | None = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str | None = None,
    sort_order: str = "asc"
) -> list[DiagramType]:
    """List Diagrams with optional filtering and pagination."""
    context: GraphQLContext = info.context
    service = context.get_service("diagram_service")
    
    # Build query parameters
    query_params = {}
    
    if filter:
        # Convert filter input to service parameters
        if hasattr(filter, 'name_contains') and filter.name_contains:
            query_params['name_contains'] = filter.name_contains
        if hasattr(filter, 'name') and filter.name is not None:
            query_params['name'] = filter.name
        if hasattr(filter, 'author') and filter.author is not None:
            query_params['author'] = filter.author

    
    # Get entities from service
    entities = await service.list(
        **query_params,
        limit=min(limit, 100),
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return entities