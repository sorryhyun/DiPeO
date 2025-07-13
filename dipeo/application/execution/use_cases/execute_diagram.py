# Use case for executing a complete diagram.

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional, Callable, Dict

from dipeo.core import BaseService
from dipeo.models import ExecutionStatus

from dipeo.application.execution.observers import StreamingObserver

if TYPE_CHECKING:
    from dipeo.core.ports.state_store import StateStorePort
    from dipeo.core.ports.message_router import MessageRouterPort
    from dipeo.infra.persistence.diagram import DiagramStorageAdapter
    from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter
    from ...unified_service_registry import UnifiedServiceRegistry
    from dipeo.models import DomainDiagram
    from ..stateful_execution_typed import TypedStatefulExecution
    from dipeo.core.static.executable_diagram import ExecutableDiagram

class ExecuteDiagramUseCase(BaseService):

    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        state_store: Optional["StateStorePort"] = None,
        message_router: Optional["MessageRouterPort"] = None,
        diagram_storage_service: Optional["DiagramStorageAdapter"] = None,
    ):
        super().__init__()
        self.service_registry = service_registry
        
        # Get services from registry if not provided directly (for backward compatibility)
        self.state_store = state_store or service_registry.get("state_store")
        self.message_router = message_router or service_registry.get("message_router")
        self.diagram_storage_service = diagram_storage_service or service_registry.get("diagram_storage_service")
        
        # Validate required services
        if not self.state_store:
            raise ValueError("state_store is required but not found in service registry")
        if not self.message_router:
            raise ValueError("message_router is required but not found in service registry")
        if not self.diagram_storage_service:
            raise ValueError("diagram_storage_service is required but not found in service registry")

    async def initialize(self):
        """Initialize the service."""
        pass

    async def execute_diagram(  # type: ignore[override]
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute diagram with streaming updates."""

        # Step 1: Compile to typed diagram
        typed_diagram = await self._compile_typed_diagram(diagram)
        
        # Step 2: Initialize execution state in persistence
        await self._initialize_typed_execution_state(execution_id, typed_diagram, options)
        
        # Step 3: Create typed execution
        typed_execution = await self._create_typed_execution(typed_diagram, options, execution_id)

        # Create streaming observer for this execution
        streaming_observer = StreamingObserver(self.message_router)

        # Import EngineFactory from application package
        from ...engine_factory import EngineFactory
        
        # Create engine with factory
        engine = EngineFactory.create_engine(
            service_registry=self.service_registry,
            state_store=self.state_store,
            message_router=self.message_router,
            custom_observers=[streaming_observer],
        )

        # Subscribe to streaming updates
        update_queue = await streaming_observer.subscribe(execution_id)

        # Start execution in background
        async def run_execution():
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug("Starting engine execution")
                
                # Update state to running
                state = await self.state_store.get_state(execution_id)
                if state:
                    state.status = ExecutionStatus.RUNNING
                    state.started_at = datetime.now(timezone.utc).isoformat()
                    state.is_active = True
                    await self.state_store.save_state(state)
                
                async for _ in engine.execute(
                    typed_execution,
                    execution_id,
                    options,
                    interactive_handler,
                ):
                    pass  # Engine uses observers for updates
                    
                logger.debug("Engine execution completed")
                
                # Finalize execution state as completed
                await self._finalize_execution_state(execution_id, ExecutionStatus.COMPLETED)
                
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Engine execution failed: {e}", exc_info=True)
                
                # Finalize execution state as failed
                await self._finalize_execution_state(
                    execution_id, 
                    ExecutionStatus.FAILED,
                    error=str(e)
                )
                
                await update_queue.put(
                    {
                        "type": "execution_error",
                        "error": str(e),
                    }
                )

        # Launch execution
        asyncio.create_task(run_execution())

        # Stream updates
        while True:
            update = await update_queue.get()
            yield update

            if update.get("type") in ["execution_complete", "execution_error"]:
                break
    
    async def _compile_typed_diagram(self, diagram: Dict[str, Any]) -> "ExecutableDiagram":  # type: ignore
        """Compile diagram to typed executable format."""
        # Get the diagram loader from service registry
        from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter
        diagram_loader: DiagramLoaderAdapter = self.service_registry.get('diagram_loader')
        if not diagram_loader:
            raise ValueError("DiagramLoaderAdapter not found in service registry")
        
        # Use the infrastructure adapter to prepare the diagram
        domain_diagram = diagram_loader.prepare_diagram(diagram)
        
        # Validate execution flow using domain service
        from dipeo.domain.execution import ExecutionDomainService
        execution_domain_service = ExecutionDomainService()
        validation_result = execution_domain_service.validate_execution_flow(domain_diagram)
        
        if not validation_result.is_valid:
            critical_issues = validation_result.critical_issues
            if critical_issues:
                # Raise error for critical issues
                error_messages = [f"- {issue.message}" for issue in critical_issues]
                raise ValueError(f"Diagram validation failed:\n" + "\n".join(error_messages))
            else:
                # Log warnings for non-critical issues
                import logging
                logger = logging.getLogger(__name__)
                for warning in validation_result.warnings:
                    logger.warning(f"Diagram validation warning: {warning.message}")
        
        # Apply diagram compilation pipeline with static types
        from ...resolution import StaticDiagramCompiler
        compiler = StaticDiagramCompiler()
        
        # Get API keys if available
        api_keys = None
        if hasattr(self.service_registry, 'get'):
            api_key_service = self.service_registry.get('api_key_service')
            if api_key_service:
                # Extract API keys needed by the diagram
                api_keys = self._extract_api_keys_for_typed_diagram(domain_diagram, api_key_service)
        
        # Compile to typed diagram
        executable_diagram = compiler.compile(domain_diagram)
        # Add API keys to metadata
        if api_keys:
            executable_diagram.metadata["api_keys"] = api_keys
        
        # Store original domain diagram metadata if needed
        if domain_diagram.metadata:
            executable_diagram.metadata.update(domain_diagram.metadata.__dict__)
        
        # Copy persons data from domain diagram to executable diagram metadata
        if hasattr(domain_diagram, 'persons') and domain_diagram.persons:
            persons_dict = {}
            for person in domain_diagram.persons:
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
        
        # Register person configs from executable diagram
        await self._register_typed_person_configs(executable_diagram)
        
        return executable_diagram
    
    async def _create_typed_execution(
        self, 
        typed_diagram: "ExecutableDiagram", 
        options: Dict[str, Any],
        execution_id: str
    ) -> "TypedStatefulExecution":
        """Create typed execution with single source of truth."""
        from ..stateful_execution_typed import TypedStatefulExecution
        
        # Service registry validation
        if not hasattr(self.service_registry, 'get'):
            raise ValueError("Service registry must support 'get' method")
        
        # Get current execution state from store
        execution_state = await self.state_store.get_state(execution_id)
        if not execution_state:
            # Should have been initialized by _initialize_typed_execution_state
            raise ValueError(f"Execution state not found for {execution_id}")
        
        # Create typed stateful execution - single source of truth for state management
        typed_execution = TypedStatefulExecution(
            diagram=typed_diagram,
            execution_state=execution_state,
            max_global_iterations=options.get("max_iterations", 100)
        )
        
        # Store stateful_execution reference in execution_state for later access
        execution_state._stateful_execution = typed_execution
        
        return typed_execution
    
    async def _register_typed_person_configs(self, typed_diagram: "ExecutableDiagram") -> None:  # type: ignore
        """Register person configurations from typed diagram."""
        from dipeo.core.static.generated_nodes import PersonJobNode
        import logging
        
        log = logging.getLogger(__name__)

        conversation_service = None
        if hasattr(self.service_registry, 'get'):
            # Try the standardized name first
            conversation_service = self.service_registry.get('conversation_service')
            if not conversation_service:
                # Fall back to legacy name for backward compatibility
                conversation_service = self.service_registry.get('conversation')
        
        if conversation_service:
            # Extract person configs from typed nodes
            person_configs = {}
            for node in typed_diagram.nodes:
                if isinstance(node, PersonJobNode) and node.person_id:
                    # Use the actual person_id from the node, not the node ID
                    person_id = str(node.person_id)
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
        options: Dict[str, Any]
    ) -> None:
        """Initialize execution state for typed diagram."""
        from dipeo.models import ExecutionState, ExecutionStatus, TokenUsage
        from datetime import datetime, timezone
        
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
        )
        
        # Store initial state
        await self.state_store.save_state(initial_state)
    
    async def _finalize_execution_state(
        self,
        execution_id: str,
        status: "ExecutionStatus",
        error: Optional[str] = None
    ) -> None:
        """Finalize execution state in persistence layer."""
        from dipeo.models import ExecutionStatus
        
        # Get current state
        state = await self.state_store.get_state(execution_id)
        if state:
            if status == ExecutionStatus.COMPLETED:
                state.status = ExecutionStatus.COMPLETED
                state.ended_at = datetime.now(timezone.utc).isoformat()
                state.is_active = False
                
                # Calculate duration
                if state.started_at:
                    start = datetime.fromisoformat(state.started_at.replace('Z', '+00:00'))
                    end = datetime.now(timezone.utc)
                    state.duration_seconds = (end - start).total_seconds()
            elif status == ExecutionStatus.FAILED:
                state.status = ExecutionStatus.FAILED
                state.ended_at = datetime.now(timezone.utc).isoformat()
                state.is_active = False
                state.error = error or "Unknown error"
            
            # Save final state
            await self.state_store.save_state(state)
    
    def _extract_api_keys_for_typed_diagram(self, diagram: "DomainDiagram", api_key_service) -> Dict[str, str]:
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
        if hasattr(diagram, 'persons'):
            for person in diagram.persons:
                api_key_id = None
                if hasattr(person, 'api_key_id'):
                    api_key_id = person.api_key_id
                elif hasattr(person, 'apiKeyId'):
                    api_key_id = person.apiKeyId
                    
                if api_key_id and api_key_id in all_keys:
                    api_keys[api_key_id] = all_keys[api_key_id]
        
        return api_keys