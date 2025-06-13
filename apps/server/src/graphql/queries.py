"""GraphQL query definitions."""
import strawberry
from typing import Optional, List, Dict, Any
from datetime import datetime

from .types.domain import (
    Diagram, ExecutionState, Person, ApiKey, ExecutionEvent
)
from .types.scalars import DiagramID, ExecutionID, PersonID, ApiKeyID, JSONScalar
from .types.inputs import DiagramFilterInput, ExecutionFilterInput
from .types.enums import NodeType, LLMService

@strawberry.type
class Query:
    """Root query type for DiPeO GraphQL API."""
    
    @strawberry.field
    async def diagram(self, id: DiagramID, info) -> Optional[Diagram]:
        """Get a single diagram by ID."""
        from .resolvers import diagram_resolver
        return await diagram_resolver.get_diagram(id, info)
    
    @strawberry.field
    async def diagrams(
        self, 
        info,
        filter: Optional[DiagramFilterInput] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Diagram]:
        """List diagrams with optional filtering."""
        from .resolvers import diagram_resolver
        return await diagram_resolver.list_diagrams(filter, limit, offset, info)
    
    @strawberry.field
    async def execution(self, id: ExecutionID, info) -> Optional[ExecutionState]:
        """Get a single execution by ID."""
        from .resolvers import execution_resolver
        return await execution_resolver.get_execution(id, info)
    
    @strawberry.field
    async def executions(
        self,
        info,
        filter: Optional[ExecutionFilterInput] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ExecutionState]:
        """List executions with optional filtering."""
        from .resolvers import execution_resolver
        return await execution_resolver.list_executions(filter, limit, offset, info)
    
    @strawberry.field
    async def execution_events(
        self,
        execution_id: ExecutionID,
        info,
        since_sequence: Optional[int] = None,
        limit: int = 1000
    ) -> List[ExecutionEvent]:
        """Get execution events for a specific execution."""
        from .resolvers import execution_resolver
        return await execution_resolver.get_execution_events(
            execution_id, since_sequence, limit, info
        )
    
    @strawberry.field
    async def person(self, id: PersonID, info) -> Optional[Person]:
        """Get a single person by ID."""
        from .resolvers import person_resolver
        return await person_resolver.get_person(id, info)
    
    @strawberry.field
    async def persons(self, info, limit: int = 100) -> List[Person]:
        """List all persons."""
        from .resolvers import person_resolver
        return await person_resolver.list_persons(limit, info)
    
    @strawberry.field
    async def api_key(self, id: ApiKeyID, info) -> Optional[ApiKey]:
        """Get a single API key by ID."""
        from .resolvers import person_resolver
        return await person_resolver.get_api_key(id, info)
    
    @strawberry.field
    async def api_keys(self, info, service: Optional[str] = None) -> List[ApiKey]:
        """List all API keys, optionally filtered by service."""
        from .resolvers import person_resolver
        return await person_resolver.list_api_keys(service, info)
    
    @strawberry.field
    async def available_models(self, service: str, api_key_id: ApiKeyID, info) -> List[str]:
        """Get available models for a service and API key."""
        from .resolvers import person_resolver
        return await person_resolver.get_available_models(service, api_key_id, info)
    
    @strawberry.field
    async def system_info(self, info) -> JSONScalar:
        """Get system information and capabilities."""
        return {
            "version": "2.0.0",
            "supported_node_types": [t.value for t in NodeType],
            "supported_llm_services": [s.value for s in LLMService],
            "max_upload_size_mb": 100,
            "websocket_url": "/api/ws",
            "graphql_subscriptions_enabled": True
        }