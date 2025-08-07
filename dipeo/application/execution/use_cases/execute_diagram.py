
import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.core import BaseService
from dipeo.diagram_generated.enums import ExecutionStatus
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
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.infrastructure.adapters.storage import DiagramStorageAdapter
    from dipeo.diagram_generated import DomainDiagram

    from ...registry import ServiceRegistry
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
    ) -> AsyncGenerator[dict[str, Any]]:
        """Execute diagram with streaming updates."""

        typed_diagram = await self._compile_typed_diagram(diagram)
        await self._initialize_typed_execution_state(execution_id, typed_diagram, options)
        
        # Always use unified monitoring
        from dipeo.application.execution.observers.unified_event_observer import UnifiedEventObserver
        import logging

        logger = logging.getLogger(__name__)
        # If observers are provided (e.g., for sub-diagrams), use them
        if observers is not None:
            engine_observers = observers
        else:
            # Create unified observer for real-time updates
            unified_observer = UnifiedEventObserver(
                message_router=self.message_router,
                execution_runtime=typed_diagram,
                capture_logs=True  # Always enable log capture
            )
            engine_observers = [unified_observer]
            # logger.debug(f"[ExecuteDiagram] Created UnifiedEventObserver for execution {execution_id}")
        from dipeo.application.execution.typed_engine import TypedExecutionEngine
        from dipeo.application.execution.resolvers import StandardRuntimeResolver
        from dipeo.application.registry.keys import EVENT_BUS
        
        runtime_resolver = StandardRuntimeResolver()
        
        # Get event bus from registry if available
        event_bus = None
        if self.service_registry.has(EVENT_BUS):
            event_bus = self.service_registry.resolve(EVENT_BUS)
            # logger.debug(f"[ExecuteDiagram] Using event bus from registry")
            
            # Subscribe unified observer to event bus using adapter
            if engine_observers:
                from dipeo.infrastructure.events.observer_adapter import ObserverToEventConsumerAdapter
                from dipeo.core.events import EventType
                
                for observer in engine_observers:
                    adapter = ObserverToEventConsumerAdapter(observer)
                    # Subscribe to all relevant event types
                    event_bus.subscribe(EventType.EXECUTION_STARTED, adapter)
                    event_bus.subscribe(EventType.NODE_STARTED, adapter)
                    event_bus.subscribe(EventType.NODE_COMPLETED, adapter)
                    event_bus.subscribe(EventType.NODE_FAILED, adapter)
                    event_bus.subscribe(EventType.EXECUTION_COMPLETED, adapter)
                    # logger.debug(f"[ExecuteDiagram] Subscribed observer to event bus")
        else:
            # logger.debug(f"[ExecuteDiagram] No event bus in registry, will use observers")
            pass
        
        # Create engine with event bus (no need for observers when using event bus)
        engine = TypedExecutionEngine(
            service_registry=self.service_registry,
            runtime_resolver=runtime_resolver,
            event_bus=event_bus,
            observers=engine_observers if not event_bus else None,
        )
        # logger.debug(f"[ExecuteDiagram] Created engine with event_bus={bool(event_bus)}, observers={bool(engine_observers if not event_bus else None)}")

        # No update iterator needed with unified monitoring

        async def run_execution():
            try:
                exec_state = await self.state_store.get_state(execution_id)
                
                # The engine will emit EXECUTION_STARTED event which triggers state updates
                async for _ in engine.execute(
                    diagram=typed_diagram,
                    execution_state=exec_state,
                    options=options,
                    container=self.container,
                    interactive_handler=interactive_handler,
                ):
                    pass

                # Engine handles completion events internally
                
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Engine execution failed: {e}", exc_info=True)
                # Error event will be emitted by the engine
                raise

        # Check if this is a sub-diagram execution (for batch parallel support)
        is_sub_diagram = options.get('is_sub_diagram', False) or options.get('parent_execution_id')
        is_batch_item = options.get('is_batch_item', False) or (options.get('metadata', {}).get('is_batch_item', False))
        
        # Create the execution task
        execution_task = asyncio.create_task(run_execution())
        
        # For sub-diagrams, we need to track the task to ensure proper parallel execution
        # Store it so the iterator below can properly coordinate
        if is_sub_diagram:
            # We'll handle this task specially in the update loop
            pass
        
        try:
            # Wait for execution completion and yield status
            if is_batch_item or is_sub_diagram:
                # Wait for the execution task to complete
                try:
                    await execution_task
                except Exception:
                    pass  # Errors are already handled in run_execution
                
                # Get final state
                state = await self.state_store.get_state(execution_id)
                # Only treat FAILED and ABORTED as errors, not PENDING or RUNNING
                is_error = state and state.status in [ExecutionStatus.FAILED, ExecutionStatus.ABORTED]
                yield {
                    "type": "execution_error" if is_error else "execution_complete",
                    "execution_id": execution_id,
                    "status": state.status.value if state else "unknown",
                    "error": state.error if state and state.error else ("Failed" if is_error else None),
                }
            else:
                # For web executions, events are consumed via MessageRouter/GraphQL subscriptions
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
                # Only treat FAILED and ABORTED as errors
                is_error = state.status in [ExecutionStatus.FAILED, ExecutionStatus.ABORTED]
                yield {
                    "type": "execution_error" if is_error else "execution_complete",
                    "execution_id": execution_id,
                    "status": state.status.value,
                    "error": state.error if state.error else ("Failed" if is_error else None),
                }
        except Exception:
            # Re-raise any exceptions
            raise
    
    async def _compile_typed_diagram(self, diagram: dict[str, Any]) -> "ExecutableDiagram":  # type: ignore
        """Compile diagram to typed executable format."""
        from dipeo.diagram_generated import DomainDiagram
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
        
        # Get compilation service from registry
        from dipeo.application.registry import COMPILATION_SERVICE
        compiler = self.service_registry.resolve(COMPILATION_SERVICE)
        if not compiler:
            raise RuntimeError("CompilationService not found in registry")
        
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

    
    async def _initialize_typed_execution_state(
        self,
        execution_id: str,
        typed_diagram: "ExecutableDiagram",  # type: ignore
        options: dict[str, Any]
    ) -> None:
        """Initialize execution state for typed diagram."""
        from datetime import datetime

        from dipeo.diagram_generated import ExecutionState, ExecutionStatus, TokenUsage
        
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