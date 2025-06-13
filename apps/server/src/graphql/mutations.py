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
from .types.domain import ApiKey, ExecutionState, Vec2
from .context import GraphQLContext

logger = logging.getLogger(__name__)

@strawberry.type
class Mutation:
    """Root mutation type for DiPeO GraphQL API."""
    
    # Diagram mutations
    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Create a new diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Create empty diagram structure
            diagram_data = {
                "nodes": {},
                "arrows": {},
                "handles": {},
                "persons": {},
                "apiKeys": {},
                "metadata": {
                    "name": input.name,
                    "description": input.description or "",
                    "author": input.author or "",
                    "tags": input.tags or [],
                    "created": datetime.now().isoformat(),
                    "modified": datetime.now().isoformat()
                }
            }
            
            # Create the diagram file
            path = diagram_service.create_diagram(input.name, diagram_data)
            
            # Convert to GraphQL type (Record to List format)
            from .types.domain import Diagram, Node, Handle, Arrow, Person, ApiKey, DiagramMetadata
            diagram = Diagram(
                nodes=[],
                handles=[],
                arrows=[],
                persons=[],
                api_keys=[],
                metadata=DiagramMetadata(
                    name=input.name,
                    description=input.description or "",
                    author=input.author or "",
                    tags=input.tags or [],
                    created=datetime.now(),
                    modified=datetime.now()
                )
            )
            
            return DiagramResult(
                success=True,
                diagram=diagram,
                message=f"Created diagram at {path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to create diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Delete a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # DiagramID is the path to the diagram file
            diagram_service.delete_diagram(id)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted diagram: {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete diagram: {str(e)}"
            )
    
    # Node mutations
    @strawberry.mutation
    async def create_node(
        self, 
        diagram_id: DiagramID, 
        input: CreateNodeInput,
        info
    ) -> NodeResult:
        """Create a new node in a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return NodeResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Generate node ID
            node_id = f"node_{str(uuid.uuid4())[:8]}"
            
            # Create node data
            node_data = {
                "id": node_id,
                "type": input.type.value,
                "position": {"x": input.position.x, "y": input.position.y},
                "data": input.properties or {}
            }
            
            # Add label to data if provided
            if input.label:
                node_data["data"]["label"] = input.label
            
            # Add node to diagram
            diagram_data["nodes"][node_id] = node_data
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert to GraphQL type
            from .types.domain import Node, Vec2
            node = Node(
                id=node_id,
                type=input.type.value,
                data=node_data["data"],
                position=Vec2(x=input.position.x, y=input.position.y)
            )
            
            return NodeResult(
                success=True,
                node=node,
                message=f"Created node {node_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create node: {e}")
            return NodeResult(
                success=False,
                error=f"Failed to create node: {str(e)}"
            )
    
    @strawberry.mutation
    async def update_node(self, input: UpdateNodeInput, info) -> NodeResult:
        """Update an existing node."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this node
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if input.id in temp_diagram.get('nodes', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return NodeResult(
                    success=False,
                    error=f"Node {input.id} not found in any diagram"
                )
            
            # Update node properties
            node = diagram_data['nodes'][input.id]
            
            if input.position:
                node['position'] = {"x": input.position.x, "y": input.position.y}
            
            if input.label is not None:
                node['data']['label'] = input.label
            
            if input.properties is not None:
                node['data'].update(input.properties)
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert to GraphQL type
            from .types.domain import Node, Vec2
            updated_node = Node(
                id=input.id,
                type=node['type'],
                data=node['data'],
                position=Vec2(x=node['position']['x'], y=node['position']['y'])
            )
            
            return NodeResult(
                success=True,
                node=updated_node,
                message=f"Updated node {input.id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update node: {e}")
            return NodeResult(
                success=False,
                error=f"Failed to update node: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_node(self, id: NodeID, info) -> DeleteResult:
        """Delete a node from a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this node
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('nodes', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Node {id} not found in any diagram"
                )
            
            # Remove node
            del diagram_data['nodes'][id]
            
            # Remove any arrows connected to this node
            arrows_to_remove = []
            for arrow_id, arrow in diagram_data.get('arrows', {}).items():
                # Check if arrow is connected to this node
                source_node_id = arrow['source'].split(':')[0]
                target_node_id = arrow['target'].split(':')[0]
                
                if source_node_id == id or target_node_id == id:
                    arrows_to_remove.append(arrow_id)
            
            for arrow_id in arrows_to_remove:
                del diagram_data['arrows'][arrow_id]
            
            # Remove any handles associated with this node
            handles_to_remove = []
            for handle_id, handle in diagram_data.get('handles', {}).items():
                if handle.get('nodeId') == id:
                    handles_to_remove.append(handle_id)
            
            for handle_id in handles_to_remove:
                del diagram_data['handles'][handle_id]
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted node {id} and {len(arrows_to_remove)} connected arrows"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete node {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete node: {str(e)}"
            )
    
    # Arrow mutations
    @strawberry.mutation
    async def create_arrow(
        self, 
        diagram_id: DiagramID,
        input: CreateArrowInput,
        info
    ) -> DiagramResult:
        """Create a new arrow between handles."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return DiagramResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Generate arrow ID
            arrow_id = f"arrow_{str(uuid.uuid4())[:8]}"
            
            # Create arrow data
            arrow_data = {
                "id": arrow_id,
                "source": input.source,
                "target": input.target,
                "data": {"label": input.label} if input.label else None
            }
            
            # Add arrow to diagram
            diagram_data["arrows"][arrow_id] = arrow_data
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert entire diagram to GraphQL type for return
            # (This is a simplified version - full conversion would be more complex)
            from .types.domain import Diagram, Node, Handle, Arrow, Person, ApiKey
            
            # Convert nodes from Record to List
            nodes = [Node(
                id=n['id'],
                type=n['type'],
                data=n.get('data', {}),
                position=Vec2(x=n['position']['x'], y=n['position']['y'])
            ) for n in diagram_data.get('nodes', {}).values()]
            
            # Convert arrows from Record to List
            arrows = [Arrow(
                id=a['id'],
                source=a['source'],
                target=a['target'],
                data=a.get('data')
            ) for a in diagram_data.get('arrows', {}).values()]
            
            # Convert other entities (simplified)
            handles = []
            persons = []
            api_keys = []
            
            diagram = Diagram(
                nodes=nodes,
                handles=handles,
                arrows=arrows,
                persons=persons,
                api_keys=api_keys
            )
            
            return DiagramResult(
                success=True,
                diagram=diagram,
                message=f"Created arrow {arrow_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create arrow: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to create arrow: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_arrow(self, id: ArrowID, info) -> DeleteResult:
        """Delete an arrow."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this arrow
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('arrows', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Arrow {id} not found in any diagram"
                )
            
            # Remove arrow
            del diagram_data['arrows'][id]
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted arrow {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete arrow {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete arrow: {str(e)}"
            )
    
    # Person mutations
    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        input: CreatePersonInput,
        info
    ) -> PersonResult:
        """Create a new person (LLM agent)."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return PersonResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Generate person ID
            person_id = f"person_{str(uuid.uuid4())[:8]}"
            
            # Create person data
            person_data = {
                "id": person_id,
                "label": input.label,
                "service": input.service.value,
                "modelName": input.model,
                "apiKeyId": input.api_key_id,
                "systemPrompt": input.system_prompt or "",
                "forgettingMode": input.forgetting_mode.value,
                "temperature": input.temperature,
                "maxTokens": input.max_tokens,
                "topP": input.top_p
            }
            
            # Add person to diagram
            if "persons" not in diagram_data:
                diagram_data["persons"] = {}
            diagram_data["persons"][person_id] = person_data
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert to GraphQL type
            from .types.domain import Person
            person = Person(
                id=person_id,
                label=input.label,
                service=input.service.value,
                modelName=input.model,
                apiKeyId=input.api_key_id,
                systemPrompt=person_data["systemPrompt"],
                forgettingMode=person_data["forgettingMode"],
                temperature=person_data["temperature"],
                maxTokens=person_data["maxTokens"],
                topP=person_data["topP"]
            )
            
            return PersonResult(
                success=True,
                person=person,
                message=f"Created person {person_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create person: {e}")
            return PersonResult(
                success=False,
                error=f"Failed to create person: {str(e)}"
            )
    
    @strawberry.mutation
    async def update_person(self, input: UpdatePersonInput, info) -> PersonResult:
        """Update an existing person."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this person
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if input.id in temp_diagram.get('persons', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return PersonResult(
                    success=False,
                    error=f"Person {input.id} not found in any diagram"
                )
            
            # Update person properties
            person = diagram_data['persons'][input.id]
            
            if input.label is not None:
                person['label'] = input.label
            if input.model is not None:
                person['modelName'] = input.model
            if input.api_key_id is not None:
                person['apiKeyId'] = input.api_key_id
            if input.system_prompt is not None:
                person['systemPrompt'] = input.system_prompt
            if input.forgetting_mode is not None:
                person['forgettingMode'] = input.forgetting_mode.value
            if input.temperature is not None:
                person['temperature'] = input.temperature
            if input.max_tokens is not None:
                person['maxTokens'] = input.max_tokens
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert to GraphQL type
            from .types.domain import Person
            updated_person = Person(
                id=input.id,
                label=person['label'],
                service=person['service'],
                modelName=person['modelName'],
                apiKeyId=person['apiKeyId'],
                systemPrompt=person.get('systemPrompt', ''),
                forgettingMode=person.get('forgettingMode', 'none'),
                temperature=person.get('temperature'),
                maxTokens=person.get('maxTokens'),
                topP=person.get('topP')
            )
            
            return PersonResult(
                success=True,
                person=updated_person,
                message=f"Updated person {input.id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update person: {e}")
            return PersonResult(
                success=False,
                error=f"Failed to update person: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_person(self, id: PersonID, info) -> DeleteResult:
        """Delete a person."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this person
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('persons', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Person {id} not found in any diagram"
                )
            
            # Remove person
            del diagram_data['persons'][id]
            
            # Update any nodes that reference this person
            nodes_updated = 0
            for node in diagram_data.get('nodes', {}).values():
                if node.get('data', {}).get('personId') == id:
                    del node['data']['personId']
                    nodes_updated += 1
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted person {id} and updated {nodes_updated} nodes"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete person {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete person: {str(e)}"
            )
    
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
        try:
            context: GraphQLContext = info.context
            event_store = context.event_store
            message_router = context.message_router
            
            # Check if execution exists
            execution = await event_store.get_execution_state(input.execution_id)
            if not execution:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {input.execution_id} not found"
                )
            
            # Create control event based on action
            from ..services.event_store import ExecutionEvent
            control_event = ExecutionEvent(
                execution_id=input.execution_id,
                sequence=0,  # Will be set by event store
                event_type=f'execution_{input.action}',
                node_id=input.node_id,
                timestamp=datetime.now(),
                data={
                    'action': input.action,
                    'node_id': input.node_id,
                    'requested_at': datetime.now().isoformat()
                }
            )
            event_store.append(control_event)
            
            # Broadcast control message via message router
            control_message = {
                'type': f'{input.action}_{"node" if input.node_id else "execution"}',
                'execution_id': input.execution_id,
                'node_id': input.node_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Route message to execution
            await message_router.broadcast_to_execution(input.execution_id, control_message)
            
            # Update execution status based on action
            new_status = _map_action_to_status(input.action, execution.get('status'))
            
            # Create updated execution state
            execution_state = ExecutionState(
                id=input.execution_id,
                status=new_status,
                diagram_id=execution.get('diagram_id'),
                started_at=datetime.fromisoformat(execution.get('started_at')),
                ended_at=datetime.fromisoformat(execution['ended_at']) if execution.get('ended_at') else None,
                running_nodes=execution.get('running_nodes', []),
                completed_nodes=execution.get('completed_nodes', []),
                skipped_nodes=execution.get('skipped_nodes', []),
                paused_nodes=execution.get('paused_nodes', []),
                failed_nodes=execution.get('failed_nodes', []),
                node_outputs=execution.get('node_outputs', {}),
                variables=execution.get('variables', {}),
                token_usage=None,
                error=None
            )
            
            return ExecutionResult(
                success=True,
                execution=execution_state,
                message=f"Execution control '{input.action}' sent successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to control execution: {e}")
            return ExecutionResult(
                success=False,
                error=f"Failed to control execution: {str(e)}"
            )
    
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


def _map_action_to_status(action: str, current_status: str):
    """Map control action to new execution status."""
    from .types.enums import ExecutionStatus
    
    # Map current status string to enum first
    current = _map_status(current_status)
    
    # Determine new status based on action
    action_map = {
        'pause': ExecutionStatus.PAUSED,
        'resume': ExecutionStatus.RUNNING,
        'abort': ExecutionStatus.CANCELLED,
        'cancel': ExecutionStatus.CANCELLED,
        'skip_node': current,  # Skip doesn't change overall execution status
    }
    
    return action_map.get(action.lower(), current)