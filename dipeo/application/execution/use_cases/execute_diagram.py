
import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.core import BaseService
from dipeo.models import ExecutionStatus
from dipeo.application.registry import (
    STATE_STORE,
    MESSAGE_ROUTER,
    DIAGRAM_STORAGE_SERVICE,
    API_KEY_SERVICE,
    CONVERSATION_SERVICE,
    CONVERSATION_MANAGER,
)

if TYPE_CHECKING:
    from dipeo.core.ports.message_router import MessageRouterPort
    from dipeo.core.ports.state_store import StateStorePort
    from dipeo.core.static.executable_diagram import ExecutableDiagram
    from dipeo.infrastructure.adapters.storage import DiagramStorageAdapter
    from dipeo.models import DomainDiagram

    from ...registry import ServiceRegistry
    from ..execution_runtime import ExecutionRuntime
    from dipeo.application.bootstrap import Container

class ExecuteDiagramUseCase(BaseService):

    def __init__(
        self,
        service_registry: "ServiceRegistry",
        state_store: Optional["StateStorePort"] = None,
        message_router: Optional["MessageRouterPort"] = None,
        diagram_storage_service: Optional["DiagramStorageAdapter"] = None,
        container: Optional["Container"] = None,
    ):
        super().__init__()
        self.service_registry = service_registry
        self.container = container
        
        self.state_store = state_store or service_registry.resolve(STATE_STORE)
        self.message_router = message_router or service_registry.resolve(MESSAGE_ROUTER)
        self.diagram_storage_service = diagram_storage_service or service_registry.resolve(DIAGRAM_STORAGE_SERVICE)
        
        if not self.state_store:
            raise ValueError("state_store is required but not found in service registry")
        if not self.message_router:
            raise ValueError("message_router is required but not found in service registry")
        if not self.diagram_storage_service:
            raise ValueError("diagram_storage_service is required but not found in service registry")

    async def initialize(self):
        pass

    async def execute_diagram(  # type: ignore[override]
        self,
        diagram: dict[str, Any],
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Callable | None = None,
        observers: list[Any] | None = None,  # Allow passing observers for sub-diagrams
        use_direct_streaming: bool = False,  # Use direct streaming instead of message router
    ) -> AsyncGenerator[dict[str, Any]]:
        """Execute diagram with streaming updates."""

        typed_diagram = await self._compile_typed_diagram(diagram)
        await self._initialize_typed_execution_state(execution_id, typed_diagram, options)
        typed_execution = await self._create_typed_execution(typed_diagram, options, execution_id)
        if observers is not None:
            engine_observers = observers
            streaming_observer = None
            for obs in observers:
                from dipeo.application.execution.observers import DirectStreamingObserver
                if isinstance(obs, DirectStreamingObserver):
                    streaming_observer = obs
                    break
            
            if not streaming_observer:
                from dipeo.application.execution.observers import DirectStreamingObserver
                streaming_observer = DirectStreamingObserver()
                engine_observers = list(observers) + [streaming_observer]
        else:
            from dipeo.application.execution.observers import DirectStreamingObserver
            
            if use_direct_streaming:
                streaming_observer = DirectStreamingObserver()
                
                try:
                    from dipeo_server.api.sse import register_observer_for_execution
                    register_observer_for_execution(execution_id, streaming_observer)
                except ImportError:
                    pass
            else:
                streaming_observer = DirectStreamingObserver()
            from dipeo.application.execution.observers import StateStoreObserver
            
            engine_observers = []
            
            if self.state_store:
                engine_observers.append(StateStoreObserver(self.state_store))
                
            engine_observers.append(streaming_observer)
        from dipeo.application.execution.engine import TypedExecutionEngine
        engine = TypedExecutionEngine(
            service_registry=self.service_registry,
            observers=engine_observers,
        )

        update_iterator = None
        if not use_direct_streaming:
            update_iterator = streaming_observer.subscribe(execution_id)

        async def run_execution():
            try:
                exec_state = await self.state_store.get_state(execution_id)
                if exec_state:
                    exec_state.status = ExecutionStatus.RUNNING
                    exec_state.started_at = datetime.now(UTC).isoformat()
                    exec_state.is_active = True
                    await self.state_store.save_state(exec_state)
                
                async for _ in engine.execute(
                    typed_execution,
                    execution_id,
                    options,
                    interactive_handler,
                ):
                    pass

                await self._finalize_execution_state(execution_id, ExecutionStatus.COMPLETED)
                
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Engine execution failed: {e}", exc_info=True)
                
                await self._finalize_execution_state(
                    execution_id, 
                    ExecutionStatus.FAILED,
                    error=str(e)
                )

        asyncio.create_task(run_execution())

        if use_direct_streaming:
            await asyncio.sleep(0.1)
            while True:
                state = await self.state_store.get_state(execution_id)
                if state and state.status in [
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.ABORTED,
                ]:
                    break
                await asyncio.sleep(1)
            yield {
                "type": "execution_complete" if state.status == ExecutionStatus.COMPLETED else "execution_error",
                "execution_id": execution_id,
                "status": state.status.value,
            }
        else:
            async for update_str in update_iterator:
                if update_str.startswith("data: "):
                    try:
                        update = json.loads(update_str[6:].strip())
                        yield update
                        
                        if update.get("type") in ["execution_complete", "execution_error"]:
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def _compile_typed_diagram(self, diagram: dict[str, Any]) -> "ExecutableDiagram":  # type: ignore
        """Compile diagram to typed executable format."""
        from dipeo.models import DomainDiagram
        from dipeo.domain.diagram.utils import dict_to_domain_diagram
        from dipeo.infrastructure.services.diagram import DiagramConverterService
        
        if isinstance(diagram, dict):
            version = diagram.get("version")
            format_type = diagram.get("format")
            
            if version in ["light", "readable"] or format_type in ["light", "readable"]:
                converter = DiagramConverterService()
                await converter.initialize()
                
                import yaml
                yaml_content = yaml.dump(diagram, default_flow_style=False, sort_keys=False)
                
                format_id = version or format_type
                domain_diagram = converter.deserialize(yaml_content, format_id)
            else:
                domain_diagram = dict_to_domain_diagram(diagram)
        elif isinstance(diagram, DomainDiagram):
            domain_diagram = diagram
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram)}")
        
        # TODO: Add updated validation logic if needed
        # Validation has been temporarily removed while updating the flow validation system
        
        from ...resolution import StaticDiagramCompiler
        compiler = StaticDiagramCompiler()
        
        api_keys = None
        if hasattr(self.service_registry, 'resolve'):
            api_key_service = self.service_registry.resolve(API_KEY_SERVICE)
            if api_key_service:
                api_keys = self._extract_api_keys_for_typed_diagram(domain_diagram, api_key_service)
        
        executable_diagram = compiler.compile(domain_diagram)
        if api_keys:
            executable_diagram.metadata["api_keys"] = api_keys
        
        if domain_diagram.metadata:
            executable_diagram.metadata.update(domain_diagram.metadata.__dict__)
        
        if hasattr(domain_diagram, 'persons') and domain_diagram.persons:
            persons_dict = {}
            persons_list = list(domain_diagram.persons.values()) if isinstance(domain_diagram.persons, dict) else domain_diagram.persons
            for person in persons_list:
                person_id = str(person.id)
                persons_dict[person_id] = {
                    'name': person.label,
                    'service': person.llm_config.service.value if hasattr(person.llm_config.service, 'value') else person.llm_config.service,
                    'model': person.llm_config.model,
                    'api_key_id': str(person.llm_config.api_key_id),
                    'system_prompt': person.llm_config.system_prompt or '',
                    'temperature': getattr(person.llm_config, 'temperature', 0.7),
                    'max_tokens': getattr(person.llm_config, 'max_tokens', None),
                }
            executable_diagram.metadata['persons'] = persons_dict
        
        await self._register_typed_person_configs(executable_diagram)
        
        return executable_diagram
    
    async def _create_typed_execution(
        self, 
        typed_diagram: "ExecutableDiagram", 
        options: dict[str, Any],
        execution_id: str
    ) -> "ExecutionRuntime":
        """Create typed execution with single source of truth."""
        from ..execution_runtime import ExecutionRuntime
        
        # Service registry validation
        if not hasattr(self.service_registry, 'get'):
            raise ValueError("Service registry must support 'get' method")
        
        # Get current execution state from store
        execution_state = await self.state_store.get_state(execution_id)
        if not execution_state:
            # Should have been initialized by _initialize_typed_execution_state
            raise ValueError(f"Execution state not found for {execution_id}")
        
        # Create execution runtime - consolidated execution management
        typed_execution = ExecutionRuntime(
            diagram=typed_diagram,
            execution_state=execution_state,
            service_registry=self.service_registry,
            container=self.container
        )
        
        # Propagate metadata from options to the execution runtime
        if options.get('metadata'):
            typed_execution.metadata.update(options['metadata'])
        
        # Store stateful_execution reference in execution_state for later access
        execution_state._stateful_execution = typed_execution
        
        return typed_execution
    
    async def _register_typed_person_configs(self, typed_diagram: "ExecutableDiagram") -> None:  # type: ignore
        """Register person configurations from typed diagram."""
        import logging

        from dipeo.diagram_generated.generated_nodes import PersonJobNode
        
        log = logging.getLogger(__name__)

        conversation_service = None
        if hasattr(self.service_registry, 'resolve'):
            # Try the standardized name first
            conversation_service = self.service_registry.resolve(CONVERSATION_SERVICE)
            if not conversation_service:
                # Fall back to conversation manager for backward compatibility
                conversation_service = self.service_registry.resolve(CONVERSATION_MANAGER)
        
        if conversation_service:
            # Extract person configs from typed nodes
            person_configs = {}
            for node in typed_diagram.nodes:
                if isinstance(node, PersonJobNode) and node.person:
                    # Use the actual person_id from the node, not the node ID
                    person_id = str(node.person)
                    # For PersonJobNode, we need to get person config from metadata or defaults
                    # The node itself only has person_id reference
                    config = {
                        'name': person_id,  # Use person ID as default name
                        'system_prompt': '',
                        'model': 'gpt-4.1-nano',
                        'temperature': 0.7,
                        'max_tokens': None,
                    }
                    
                    # Try to get person config from diagram metadata if available
                    if typed_diagram.metadata and 'persons' in typed_diagram.metadata:
                        persons_metadata = typed_diagram.metadata['persons']
                        if person_id in persons_metadata:
                            person_data = persons_metadata[person_id]
                            config.update({
                                'name': person_data.get('name', person_id),
                                'system_prompt': person_data.get('system_prompt', ''),
                                'service': person_data.get('service', 'openai'),
                                'model': person_data.get('model', 'gpt-4.1-nano'),
                                'temperature': person_data.get('temperature', 0.7),
                                'max_tokens': person_data.get('max_tokens'),
                                'api_key_id': person_data.get('api_key_id', ''),
                            })
                    
                    person_configs[person_id] = config
                    
                    # Register person if conversation service supports it
                    if hasattr(conversation_service, 'register_person'):
                        conversation_service.register_person(person_id, config)
                    else:
                        # For services that don't have register_person, 
                        # we can at least ensure the person memory is created
                        if hasattr(conversation_service, 'get_or_create_person_memory'):
                            conversation_service.get_or_create_person_memory(person_id)
            
            # Log person registrations
            if person_configs:
                log.debug(f"Registered {len(person_configs)} person configs for execution")
    
    async def _initialize_typed_execution_state(
        self,
        execution_id: str,
        typed_diagram: "ExecutableDiagram",  # type: ignore
        options: dict[str, Any]
    ) -> None:
        """Initialize execution state for typed diagram."""
        from datetime import datetime

        from dipeo.models import ExecutionState, ExecutionStatus, TokenUsage
        
        # Create initial execution state
        initial_state = ExecutionState(
            id=execution_id,
            status=ExecutionStatus.PENDING,
            diagram_id=typed_diagram.metadata.get('id') if typed_diagram.metadata else None,
            started_at=datetime.now().isoformat(),
            node_states={},
            node_outputs={},
            variables=options.get("variables", {}),
            is_active=True,
            token_usage=TokenUsage(input=0, output=0),
            exec_counts={},
            executed_nodes=[],
        )
        
        # Store initial state
        await self.state_store.save_state(initial_state)
    
    async def _finalize_execution_state(
        self,
        execution_id: str,
        status: "ExecutionStatus",
        error: str | None = None
    ) -> None:
        """Finalize execution state in persistence layer."""
        from dipeo.models import ExecutionStatus
        
        # Get current state
        state = await self.state_store.get_state(execution_id)
        if state:
            if status == ExecutionStatus.COMPLETED:
                state.status = ExecutionStatus.COMPLETED
                state.ended_at = datetime.now(UTC).isoformat()
                state.is_active = False
                
                # Calculate duration
                if state.started_at:
                    start = datetime.fromisoformat(state.started_at.replace('Z', '+00:00'))
                    end = datetime.now(UTC)
                    state.duration_seconds = (end - start).total_seconds()
            elif status == ExecutionStatus.FAILED:
                state.status = ExecutionStatus.FAILED
                state.ended_at = datetime.now(UTC).isoformat()
                state.is_active = False
                state.error = error or "Unknown error"
            
            # Save final state
            await self.state_store.save_state(state)
    
    def _extract_api_keys_for_typed_diagram(self, diagram: "DomainDiagram", api_key_service) -> dict[str, str]:
        """Extract API keys needed by the diagram.
        
        Args:
            diagram: The domain diagram (before compilation)
            api_key_service: The API key service
            
        Returns:
            Dictionary mapping API key IDs to actual keys
        """
        api_keys = {}
        
        # Get all available API keys
        all_keys = {
            info["id"]: api_key_service.get_api_key(info["id"])["key"]
            for info in api_key_service.list_api_keys()
        }
        
        # Extract API key references from persons
        if hasattr(diagram, 'persons') and diagram.persons:
            # Handle both dict and list formats
            persons_list = list(diagram.persons.values()) if isinstance(diagram.persons, dict) else diagram.persons
            for person in persons_list:
                api_key_id = None
                if hasattr(person, 'api_key_id'):
                    api_key_id = person.api_key_id
                elif hasattr(person, 'apiKeyId'):
                    api_key_id = person.apiKeyId
                elif hasattr(person, 'llm_config'):
                    # Handle nested llm_config structure
                    if hasattr(person.llm_config, 'api_key_id'):
                        api_key_id = person.llm_config.api_key_id
                    elif hasattr(person.llm_config, 'apiKeyId'):
                        api_key_id = person.llm_config.apiKeyId
                    
                if api_key_id and api_key_id in all_keys:
                    api_keys[api_key_id] = all_keys[api_key_id]
        
        return api_keys