"""GraphQL query definitions."""
import strawberry
from typing import Optional, List
from datetime import datetime

from .domain_types import (
    DomainDiagramType, ExecutionState, DomainPerson, DomainApiKey, ExecutionEvent
)
from .results_types import DiagramFormatInfo
from .scalars_types import DiagramID, ExecutionID, PersonID, ApiKeyID, JSONScalar
from .inputs_types import DiagramFilterInput, ExecutionFilterInput
# Import enums from the Pydantic models (single source of truth)
from dipeo_server.core import NodeType, LLMService

@strawberry.type
class Query:
    """Root query type for DiPeO GraphQL API."""
    
    @strawberry.field
    async def diagram(self, id: DiagramID, info) -> Optional[DomainDiagramType]:
        """Get a single diagram by ID."""
        from .diagram_resolver import diagram_resolver
        return await diagram_resolver.get_diagram(id, info)
    
    @strawberry.field
    async def diagrams(
        self, 
        info,
        filter: Optional[DiagramFilterInput] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DomainDiagramType]:
        """List diagrams with optional filtering."""
        from .diagram_resolver import diagram_resolver
        return await diagram_resolver.list_diagrams(filter, limit, offset, info)
    
    @strawberry.field
    async def execution(self, id: ExecutionID, info) -> Optional[ExecutionState]:
        """Get a single execution by ID."""
        from .execution_resolver import execution_resolver
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
        from .execution_resolver import execution_resolver
        return await execution_resolver.list_executions(filter, limit, offset, info)
    
    @strawberry.field(deprecation_reason="Events are no longer stored. Use execution state subscriptions instead.")
    async def execution_events(
        self,
        execution_id: ExecutionID,
        info,
        since_sequence: Optional[int] = None,
        limit: int = 1000
    ) -> List[ExecutionEvent]:
        """
        DEPRECATED: Get execution events for a specific execution.
        Always returns an empty list as events are no longer stored.
        """
        from .execution_resolver import execution_resolver
        return await execution_resolver.get_execution_events(
            execution_id, since_sequence, limit, info
        )
    
    @strawberry.field
    async def person(self, id: PersonID, info) -> Optional[DomainPerson]:
        """Get a single person by ID."""
        from .person_resolver import person_resolver
        return await person_resolver.get_person(id, info)
    
    @strawberry.field
    async def persons(self, info, limit: int = 100) -> List[DomainPerson]:
        """List all persons."""
        from .person_resolver import person_resolver
        return await person_resolver.list_persons(limit, info)
    
    @strawberry.field
    async def api_key(self, id: ApiKeyID, info) -> Optional[DomainApiKey]:
        """Get a single API key by ID."""
        from .person_resolver import person_resolver
        return await person_resolver.get_api_key(id, info)
    
    @strawberry.field
    async def api_keys(self, info, service: Optional[str] = None) -> List[DomainApiKey]:
        """List all API keys, optionally filtered by service."""
        from .person_resolver import person_resolver
        return await person_resolver.list_api_keys(service, info)
    
    @strawberry.field
    async def available_models(self, service: str, api_key_id: ApiKeyID, info) -> List[str]:
        """Get available models for a service and API key."""
        from .person_resolver import person_resolver
        return await person_resolver.get_available_models(service, api_key_id, info)
    
    @strawberry.field
    async def system_info(self, info) -> JSONScalar:
        """Get system information and capabilities."""
        return {
            "version": "2.0.0",
            "supported_node_types": [t.value for t in NodeType],
            "supported_llm_services": [s.value for s in LLMService],
            "max_upload_size_mb": 100,
            "graphql_subscriptions_enabled": True
        }
    
    @strawberry.field
    async def execution_capabilities(self, info) -> JSONScalar:
        """Get information about execution capabilities (replaces REST endpoint)."""
        context = info.context
        
        diagram_service = context.diagram_service
        persons_list = []
        
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
        
        checks = {
            "database": False,
            "redis": False,
            "file_system": False
        }
        
        try:
            await context.state_store.list_executions(limit=1)
            checks["database"] = True
        except:
            pass
        
        checks["redis"] = False  # Redis is being removed
        
        try:
            import os
            os.path.exists("files/diagrams")
            checks["file_system"] = True
        except:
            pass
        
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
        
        all_conversations = []
        
        if not hasattr(memory_service, 'person_memories') or not memory_service.person_memories:
            return {
                "conversations": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
        
        for person_id_key, person_memory in memory_service.person_memories.items():
            if person_id and person_id_key != person_id:
                continue
            
            for message in person_memory.messages:
                is_forgotten = message.id in person_memory.forgotten_message_ids
                if not show_forgotten and is_forgotten:
                    continue
                
                if execution_id and message.execution_id != execution_id:
                    continue
                
                if search:
                    search_lower = search.lower()
                    if not any(search_lower in str(v).lower() for v in [
                        message.content,
                        message.node_label or '',
                        message.node_id or ''
                    ]):
                        continue
                
                if since and message.timestamp < since:
                    continue
                
                conversation = {
                    "id": message.id,
                    "personId": person_id_key,
                    "executionId": message.execution_id,
                    "nodeId": message.node_id,
                    "nodeLabel": message.node_label,
                    "timestamp": message.timestamp.isoformat(),
                    "userPrompt": "",  # Not stored separately in new system
                    "assistantResponse": message.content,
                    "forgotten": is_forgotten,
                    "tokenUsage": {
                        "total": message.token_count or 0,
                        "input": message.input_tokens or 0,
                        "output": message.output_tokens or 0,
                        "cached": message.cached_tokens or 0
                    } if message.token_count else None
                }
                all_conversations.append(conversation)
        
        all_conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        paginated = all_conversations[offset:offset + limit]
        
        return {
            "conversations": paginated,
            "total": len(all_conversations),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(all_conversations)
        }
    
    @strawberry.field
    async def supported_formats(self, info) -> List[DiagramFormatInfo]:
        """Get list of supported diagram formats for import/export."""
        from dipeo_server.domains.diagram.converters import converter_registry
        
        formats = converter_registry.list_formats()
        return [
            DiagramFormatInfo(
                id=fmt['id'],
                name=fmt['name'],
                description=fmt['description'],
                extension=fmt['extension'],
                supports_import=fmt.get('supports_import', True),
                supports_export=fmt.get('supports_export', True)
            )
            for fmt in formats
        ]