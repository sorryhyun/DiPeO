"""GraphQL queries for DiPeO.

These queries use the ServiceRegistry to access application services,
keeping GraphQL concerns separate from business logic.
"""

from datetime import datetime

import strawberry
from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry

# Import domain models for type hints
from dipeo.diagram_generated.domain_models import DiagramID, ExecutionID, PersonID

# Import Strawberry types
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainPersonType,
    ExecutionStateType,
)
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput, ExecutionFilterInput

from ..types.cli_session import CliSession
from ..types.provider_types import (
    OperationSchemaType,
    OperationType,
    ProviderStatisticsType,
    ProviderType,
)
from ..types.query_types import DiagramFormatInfo

# Import standalone query resolvers
from .query_resolvers import (
    get_active_cli_session,
    get_api_key,
    get_api_keys,
    get_available_models,
    get_diagram,
    get_execution,
    get_execution_capabilities,
    get_execution_history,
    get_execution_metrics,
    get_execution_order,
    get_operation_schema,
    get_person,
    get_prompt_file,
    get_provider,
    get_provider_operations,
    get_provider_statistics,
    get_providers,
    get_supported_formats,
    get_system_info,
    health_check,
    list_conversations,
    list_diagrams,
    list_executions,
    list_persons,
    list_prompt_files,
)


def create_query_type(registry: ServiceRegistry) -> type:
    """Create Query type with injected service registry."""

    @strawberry.type
    class Query:
        @strawberry.field
        async def diagram(self, id: strawberry.ID) -> DomainDiagramType | None:
            """Query method that delegates to standalone resolver."""
            return await get_diagram(registry, id)

        @strawberry.field
        async def diagrams(
            self,
            filter: DiagramFilterInput | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[DomainDiagramType]:
            """Query method that delegates to standalone resolver."""
            return await list_diagrams(registry, filter, limit, offset)

        @strawberry.field
        async def execution(self, id: strawberry.ID) -> ExecutionStateType | None:
            """Query method that delegates to standalone resolver."""
            return await get_execution(registry, id)

        @strawberry.field
        async def executions(
            self,
            filter: ExecutionFilterInput | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[ExecutionStateType]:
            """Query method that delegates to standalone resolver."""
            return await list_executions(registry, filter, limit, offset)

        @strawberry.field
        async def person(self, id: strawberry.ID) -> DomainPersonType | None:
            """Query method that delegates to standalone resolver."""
            return await get_person(registry, id)

        @strawberry.field
        async def persons(self, limit: int = 100) -> list[DomainPersonType]:
            """Query method that delegates to standalone resolver."""
            return await list_persons(registry, limit)

        @strawberry.field
        async def api_key(self, id: strawberry.ID) -> DomainApiKeyType | None:
            """Query method that delegates to standalone resolver."""
            return await get_api_key(registry, id)

        @strawberry.field
        async def api_keys(self, service: str | None = None) -> list[DomainApiKeyType]:
            """Query method that delegates to standalone resolver."""
            return await get_api_keys(registry, service)

        @strawberry.field
        async def available_models(self, service: str, api_key_id: strawberry.ID) -> list[str]:
            """Query method that delegates to standalone resolver."""
            return await get_available_models(registry, service, api_key_id)

        @strawberry.field
        async def providers(self) -> list[ProviderType]:
            """Query method that delegates to standalone resolver."""
            return await get_providers(registry)

        @strawberry.field
        async def provider(self, name: str) -> ProviderType | None:
            """Query method that delegates to standalone resolver."""
            return await get_provider(registry, name)

        @strawberry.field
        async def provider_operations(self, provider: str) -> list[OperationType]:
            """Query method that delegates to standalone resolver."""
            return await get_provider_operations(registry, provider)

        @strawberry.field
        async def operation_schema(
            self, provider: str, operation: str
        ) -> OperationSchemaType | None:
            """Query method that delegates to standalone resolver."""
            return await get_operation_schema(registry, provider, operation)

        @strawberry.field
        async def provider_statistics(self) -> ProviderStatisticsType:
            """Query method that delegates to standalone resolver."""
            return await get_provider_statistics(registry)

        @strawberry.field
        async def system_info(self) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await get_system_info(registry)

        @strawberry.field
        async def execution_capabilities(self) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await get_execution_capabilities(registry)

        @strawberry.field
        async def health(self) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await health_check(registry)

        @strawberry.field
        async def conversations(
            self,
            person_id: strawberry.ID | None = None,
            execution_id: strawberry.ID | None = None,
            search: str | None = None,
            show_forgotten: bool = False,
            limit: int = 100,
            offset: int = 0,
            since: datetime | None = None,
        ) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await list_conversations(
                registry, person_id, execution_id, search, show_forgotten, limit, offset, since
            )

        @strawberry.field
        async def supported_formats(self) -> list[DiagramFormatInfo]:
            """Query method that delegates to standalone resolver."""
            return await get_supported_formats(registry)

        @strawberry.field
        async def execution_order(self, execution_id: strawberry.ID) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await get_execution_order(registry, execution_id)

        @strawberry.field
        async def prompt_files(self) -> list[JSON]:
            """Query method that delegates to standalone resolver."""
            return await list_prompt_files(registry)

        @strawberry.field
        async def prompt_file(self, filename: str) -> JSON:
            """Query method that delegates to standalone resolver."""
            return await get_prompt_file(registry, filename)

        @strawberry.field
        async def active_cli_session(self) -> CliSession | None:
            """Query method that delegates to standalone resolver."""
            return await get_active_cli_session(registry)

        @strawberry.field
        async def execution_metrics(self, execution_id: strawberry.ID) -> JSON | None:
            """Query method that delegates to standalone resolver."""
            return await get_execution_metrics(registry, execution_id)

        @strawberry.field
        async def execution_history(
            self,
            diagram_id: strawberry.ID | None = None,
            limit: int = 100,
            include_metrics: bool = False,
        ) -> list[ExecutionStateType]:
            """Query method that delegates to standalone resolver."""
            return await get_execution_history(registry, diagram_id, limit, include_metrics)

    return Query
