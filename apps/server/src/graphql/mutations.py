"""GraphQL mutation definitions."""
import strawberry
from typing import Optional
import logging
import uuid
from datetime import datetime

from .types.results import (
    DiagramResult, ExecutionResult, NodeResult, PersonResult,
    ApiKeyResult, DeleteResult, TestApiKeyResult
)
from .types.scalars import DiagramID, ExecutionID, NodeID, PersonID, ApiKeyID, ArrowID
from .types.inputs import (
    CreateDiagramInput, CreateNodeInput, UpdateNodeInput,
    CreateArrowInput, CreatePersonInput, UpdatePersonInput,
    CreateApiKeyInput, ExecuteDiagramInput, ExecutionControlInput,
    InteractiveResponseInput
)
from .types.domain import ApiKey, ExecutionState
from .context import GraphQLContext

logger = logging.getLogger(__name__)

@strawberry.type
class Mutation:
    """Root mutation type for DiPeO GraphQL API."""
    
    # Diagram mutations
    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Create a new diagram."""
        # Implementation will call diagram service
        pass
    
    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Delete a diagram."""
        pass
    
    # Node mutations
    @strawberry.mutation
    async def create_node(
        self, 
        diagram_id: DiagramID, 
        input: CreateNodeInput,
        info
    ) -> NodeResult:
        """Create a new node in a diagram."""
        pass
    
    @strawberry.mutation
    async def update_node(self, input: UpdateNodeInput, info) -> NodeResult:
        """Update an existing node."""
        pass
    
    @strawberry.mutation
    async def delete_node(self, id: NodeID, info) -> DeleteResult:
        """Delete a node from a diagram."""
        pass
    
    # Arrow mutations
    @strawberry.mutation
    async def create_arrow(
        self, 
        diagram_id: DiagramID,
        input: CreateArrowInput,
        info
    ) -> DiagramResult:
        """Create a new arrow between handles."""
        pass
    
    @strawberry.mutation
    async def delete_arrow(self, id: ArrowID, info) -> DeleteResult:
        """Delete an arrow."""
        pass
    
    # Person mutations
    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        input: CreatePersonInput,
        info
    ) -> PersonResult:
        """Create a new person (LLM agent)."""
        pass
    
    @strawberry.mutation
    async def update_person(self, input: UpdatePersonInput, info) -> PersonResult:
        """Update an existing person."""
        pass
    
    @strawberry.mutation
    async def delete_person(self, id: PersonID, info) -> DeleteResult:
        """Delete a person."""
        pass
    
    # API Key mutations
    @strawberry.mutation
    async def create_api_key(self, input: CreateApiKeyInput, info) -> ApiKeyResult:
        """Create a new API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Create API key
            api_key_data = api_key_service.create_api_key(
                label=input.label,
                service=input.service.value,
                key=input.key
            )
            
            # Convert to GraphQL type
            api_key = ApiKey(
                id=api_key_data['id'],
                label=api_key_data['label'],
                service=input.service
            )
            
            return ApiKeyResult(
                success=True,
                api_key=api_key
            )
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            return ApiKeyResult(
                success=False,
                error=f"Failed to create API key: {str(e)}"
            )
    
    @strawberry.mutation
    async def test_api_key(self, id: ApiKeyID, info) -> TestApiKeyResult:
        """Test an API key to verify it works."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            llm_service = context.llm_service
            
            # Get API key
            api_key_data = api_key_service.get_api_key(id)
            if not api_key_data:
                return TestApiKeyResult(
                    success=False,
                    valid=False,
                    error="API key not found"
                )
            
            # Test the API key by getting available models
            try:
                models = llm_service.get_available_models(
                    service=api_key_data['service'],
                    api_key_id=id
                )
                
                return TestApiKeyResult(
                    success=True,
                    valid=True,
                    available_models=models
                )
                
            except Exception as test_error:
                return TestApiKeyResult(
                    success=True,
                    valid=False,
                    error=f"API key test failed: {str(test_error)}"
                )
                
        except Exception as e:
            logger.error(f"Failed to test API key {id}: {e}")
            return TestApiKeyResult(
                success=False,
                valid=False,
                error=f"Failed to test API key: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_api_key(self, id: ApiKeyID, info) -> DeleteResult:
        """Delete an API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Delete API key
            api_key_service.delete_api_key(id)
            
            return DeleteResult(
                success=True,
                deleted_id=id
            )
            
        except Exception as e:
            logger.error(f"Failed to delete API key {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete API key: {str(e)}"
            )
    
    # Execution mutations
    @strawberry.mutation
    async def execute_diagram(self, input: ExecuteDiagramInput, info) -> ExecutionResult:
        """Start executing a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            execution_service = context.execution_service
            event_store = context.event_store
            message_router = context.message_router
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(input.diagram_id)
            if not diagram_data:
                return ExecutionResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Prepare options
            options = {
                'debugMode': input.debug_mode or False,
                'maxIterations': input.max_iterations or 100,
                'timeout': input.timeout_seconds or 600
            }
            
            # Create initial execution state event
            from ..services.event_store import ExecutionEvent
            initial_event = ExecutionEvent(
                execution_id=execution_id,
                sequence=0,
                event_type='execution_started',
                node_id=None,
                timestamp=datetime.now(),
                data={
                    'diagram_id': input.diagram_id,
                    'options': options,
                    'status': 'started'
                }
            )
            event_store.append(initial_event)
            
            # Start execution in background
            # Note: In a real implementation, this would start the execution
            # asynchronously and return immediately. The client would then
            # subscribe to updates via GraphQL subscriptions.
            
            # For now, return the initial state
            execution = ExecutionState(
                id=execution_id,
                status=_map_status('started'),
                diagram_id=input.diagram_id,
                started_at=datetime.now(),
                ended_at=None,
                running_nodes=[],
                completed_nodes=[],
                skipped_nodes=[],
                paused_nodes=[],
                failed_nodes=[],
                node_outputs={},
                variables={},
                token_usage=None,
                error=None
            )
            
            return ExecutionResult(
                success=True,
                execution=execution
            )
            
        except Exception as e:
            logger.error(f"Failed to execute diagram: {e}")
            return ExecutionResult(
                success=False,
                error=f"Failed to execute diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def control_execution(
        self, 
        input: ExecutionControlInput,
        info
    ) -> ExecutionResult:
        """Control a running execution (pause, resume, abort, skip)."""
        pass
    
    @strawberry.mutation
    async def submit_interactive_response(
        self,
        input: InteractiveResponseInput,
        info
    ) -> ExecutionResult:
        """Submit a response to an interactive prompt."""
        pass
    
    @strawberry.mutation
    async def clear_conversations(self, info) -> DeleteResult:
        """Clear all conversation history."""
        try:
            context: GraphQLContext = info.context
            memory_service = context.memory_service
            
            # Clear all conversations
            memory_service.clear_all_conversations()
            
            return DeleteResult(
                success=True,
                message="All conversations cleared"
            )
            
        except Exception as e:
            logger.error(f"Failed to clear conversations: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to clear conversations: {str(e)}"
            )


def _map_status(status: str):
    """Map internal status string to GraphQL ExecutionStatus enum."""
    from .types.enums import ExecutionStatus
    status_map = {
        'started': ExecutionStatus.STARTED,
        'running': ExecutionStatus.RUNNING,
        'paused': ExecutionStatus.PAUSED,
        'completed': ExecutionStatus.COMPLETED,
        'failed': ExecutionStatus.FAILED,
        'cancelled': ExecutionStatus.CANCELLED
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)