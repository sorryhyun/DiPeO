"""GraphQL queries for Execution - Auto-generated."""

import strawberry
from typing import Optional

from dipeo_server.api.graphql.context import GraphQLContext
from dipeo_server.api.graphql.generated.types import (
    ExecutionID,
    ExecutionType,
    ExecutionFilterInput,
    JSONScalar,
)


@strawberry.field
async def execution(
    self,
    id: ExecutionID,
    info: strawberry.Info[GraphQLContext]
) -> ExecutionType | None:
    """Get a single Execution by ID."""
    context: GraphQLContext = info.context
    service = context.get_service("execution_service")
    
    entity = await service.get(id)
    
    if not entity:
        raise ValueError(f"Execution with ID {id} not found")
    
    return entity

@strawberry.field
async def Executions(
    self,
    info: strawberry.Info[GraphQLContext],
    filter: ExecutionFilterInput | None = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str | None = None,
    sort_order: str = "asc"
) -> list[ExecutionType]:
    """List Executions with optional filtering and pagination."""
    context: GraphQLContext = info.context
    service = context.get_service("execution_service")
    
    # Build query parameters
    query_params = {}
    
    if filter:
        # Convert filter input to service parameters
        if hasattr(filter, 'name_contains') and filter.name_contains:
            query_params['name_contains'] = filter.name_contains
        if hasattr(filter, 'diagram_id') and filter.diagram_id is not None:
            query_params['diagram_id'] = filter.diagram_id
        if hasattr(filter, 'status') and filter.status is not None:
            query_params['status'] = filter.status

    
    # Get entities from service
    entities = await service.list(
        **query_params,
        limit=min(limit, 100),
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return entities