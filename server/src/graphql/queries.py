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
    
    @strawberry.field
    async def execution_capabilities(self, info) -> JSONScalar:
        """Get information about execution capabilities (replaces REST endpoint)."""
        context = info.context
        
        # Get available person IDs
        diagram_service = context.diagram_service
        persons_list = []
        
        # Scan diagrams for persons
        diagrams = diagram_service.list_diagram_files()
        for diagram_meta in diagrams:
            diagram = diagram_service.load_diagram(diagram_meta['path'])
            for person_id, person_data in diagram.get('persons', {}).items():
                persons_list.append({
                    'id': person_id,
                    'name': person_data.get('name', ''),
                    'model': person_data.get('modelName', 'gpt-4o-mini'),
                    'apiKeyId': person_data.get('apiKeyId')
                })
        
        return {
            "supported_node_types": [t.value for t in NodeType],
            "supported_llm_services": [s.value for s in LLMService],
            "available_persons": persons_list,
            "execution_features": {
                "interactive_prompts": True,
                "pause_resume": True,
                "node_skip": True,
                "real_time_updates": True,
                "token_tracking": True
            }
        }
    
    @strawberry.field
    async def health(self, info) -> JSONScalar:
        """Health check endpoint (replaces REST endpoint)."""
        context = info.context
        
        # Check various services
        checks = {
            "database": False,
            "redis": False,
            "file_system": False
        }
        
        # Check database (event store)
        try:
            await context.event_store.list_executions(limit=1)
            checks["database"] = True
        except:
            pass
        
        # Check Redis
        try:
            redis_client = getattr(context.event_store, '_redis_client', None)
            if redis_client:
                await redis_client.ping()
                checks["redis"] = True
        except:
            pass
        
        # Check file system
        try:
            import os
            os.path.exists("files/diagrams")
            checks["file_system"] = True
        except:
            pass
        
        # Overall status
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "version": "2.0.0"
        }
    
    @strawberry.field
    async def conversations(
        self,
        info,
        person_id: Optional[PersonID] = None,
        execution_id: Optional[ExecutionID] = None,
        search: Optional[str] = None,
        show_forgotten: bool = False,
        limit: int = 100,
        offset: int = 0,
        since: Optional[datetime] = None
    ) -> JSONScalar:
        """Get conversation data with filtering (replaces REST endpoint)."""
        context = info.context
        memory_service = context.memory_service
        
        # Get all conversations
        all_conversations = memory_service.get_all_conversations()
        
        # Filter conversations
        filtered = []
        for person_id_key, conversations in all_conversations.items():
            # Filter by person_id if specified
            if person_id and person_id_key != person_id:
                continue
            
            for conv in conversations:
                # Filter by execution_id if specified
                if execution_id and conv.get('executionId') != execution_id:
                    continue
                
                # Filter by search term if specified
                if search:
                    search_lower = search.lower()
                    if not any(search_lower in str(v).lower() for v in [
                        conv.get('userPrompt', ''),
                        conv.get('assistantResponse', ''),
                        conv.get('nodeId', '')
                    ]):
                        continue
                
                # Filter by forgotten status
                if not show_forgotten and conv.get('forgotten', False):
                    continue
                
                # Filter by time if specified
                if since:
                    conv_time = datetime.fromisoformat(conv.get('timestamp', ''))
                    if conv_time < since:
                        continue
                
                # Add person_id to conversation for clarity
                conv['personId'] = person_id_key
                filtered.append(conv)
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        paginated = filtered[offset:offset + limit]
        
        return {
            "conversations": paginated,
            "total": len(filtered),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(filtered)
        }