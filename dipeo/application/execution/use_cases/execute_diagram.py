"""Use case for executing a complete diagram."""

import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional, Callable, Dict

from dipeo.core import BaseService, SupportsExecution

from dipeo.application.execution.observers import StreamingObserver
from dipeo.application.execution.state import UnifiedExecutionCoordinator

if TYPE_CHECKING:
    from dipeo.core.ports.state_store import StateStorePort
    from dipeo.core.ports.message_router import MessageRouterPort
    from dipeo.infra.persistence.diagram import DiagramStorageAdapter
    from ...unified_service_registry import UnifiedServiceRegistry
    from dipeo.models import DomainDiagram, ExecutionStatus
    from ... import ExecutionController

class ExecuteDiagramUseCase(BaseService, SupportsExecution):
    """High-level orchestration for diagram execution."""

    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        state_store: "StateStorePort",
        message_router: "MessageRouterPort",
        diagram_storage_service: "DiagramStorageAdapter",
    ):
        super().__init__()
        self.service_registry = service_registry
        self.state_store = state_store
        self.message_router = message_router
        self.diagram_storage_service = diagram_storage_service
        self.coordinator = UnifiedExecutionCoordinator(
            service_registry=service_registry
        )

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

        # Prepare diagram
        diagram_obj = await self._prepare_diagram(diagram)
        
        # Initialize execution state in persistence first
        await self._initialize_execution_state(execution_id, diagram_obj, options)
        
        # Setup execution context (which needs the state to exist)
        controller = await self._setup_execution_context(diagram_obj, options, execution_id)

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
                    self.coordinator.transition_to_running(state)
                    await self.state_store.save_state(state)
                
                async for _ in engine.execute_prepared(
                    diagram_obj,
                    controller,
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
    
    async def _prepare_diagram(self, diagram: Dict[str, Any]) -> "DomainDiagram":
        """Prepare and convert diagram to domain format."""
        # Get the diagram loader from service registry
        diagram_loader = self.service_registry.get('diagram_loader')
        if not diagram_loader:
            raise ValueError("DiagramLoaderPort not found in service registry")
        
        # Use the infrastructure adapter to prepare the diagram
        domain_diagram = diagram_loader.prepare_diagram(diagram)
        
        # Apply diagram resolution pipeline
        from ...resolution import DiagramResolver
        resolver = DiagramResolver()
        
        # Note: The resolver returns an ExecutableDiagram, but for backward
        # compatibility, we'll store it in the domain_diagram metadata
        # and use it in the execution engine
        executable_diagram = await resolver.resolve(domain_diagram)
        
        # Store the executable diagram in metadata for use by the engine
        if not hasattr(domain_diagram, '_executable_diagram'):
            domain_diagram._executable_diagram = executable_diagram
        
        return domain_diagram
    
    async def _setup_execution_context(
        self, 
        diagram: "DomainDiagram", 
        options: Dict[str, Any],
        execution_id: str
    ) -> "ExecutionController":
        """Setup execution context including controller and state."""
        from ...engine.execution_controller import ExecutionController
        
        # Get required domain services
        if not hasattr(self.service_registry, 'get'):
            raise ValueError("Service registry must support 'get' method")
            
        flow_control_service = self.service_registry.get('flow_control_service')
        if not flow_control_service:
            # Try legacy name for backward compatibility
            flow_control_service = self.service_registry.get('execution_flow_service')
        
        if not flow_control_service:
            raise ValueError("FlowControlService is required but not found in service registry")
        
        # Get current execution state from store
        execution_state = await self.state_store.get_state(execution_id)
        if not execution_state:
            # Should have been initialized by _initialize_execution_state
            raise ValueError(f"Execution state not found for {execution_id}")
        
        # Create state adapter
        from ..adapters.state_adapter import ApplicationExecutionState
        state_adapter = ApplicationExecutionState(
            execution_state=execution_state,
            state_store=self.state_store
        )
        
        # Create controller with state adapter
        controller = ExecutionController(
            flow_control_service=flow_control_service,
            state_adapter=state_adapter,
            max_global_iterations=options.get("max_iterations", 100)
        )
        
        # Initialize controller with nodes from diagram
        await controller.initialize_nodes(diagram)
        
        # Register person configs with conversation service
        await self._register_person_configs(diagram)
        
        return controller
    
    async def _register_person_configs(self, diagram: "DomainDiagram") -> None:
        """Register person configurations with conversation service and create minimal context."""
        from dipeo.models import NodeType
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
            # Extract person configs from diagram
            person_configs = {}
            for node in diagram.nodes:
                if node.type == NodeType.person_job.value:
                    person_id = node.id
                    # Extract person config from node data
                    if hasattr(node, 'data') and node.data:
                        config = {
                            'name': node.data.get('name', person_id),
                            'system_prompt': node.data.get('system_prompt', ''),
                            'model': node.data.get('model', 'gpt-4.1-nano'),
                            'temperature': node.data.get('temperature', 0.7),
                            'max_tokens': node.data.get('max_tokens'),
                        }
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
    
    async def _initialize_execution_state(
        self,
        execution_id: str,
        diagram: "DomainDiagram",
        options: Dict[str, Any]
    ) -> None:
        """Initialize execution state in persistence layer."""
        from dipeo.models import ExecutionState, ExecutionStatus, TokenUsage
        from datetime import datetime
        
        # Create initial execution state
        initial_state = ExecutionState(
            id=execution_id,
            status=ExecutionStatus.PENDING,
            diagram_id=diagram.metadata.id if diagram.metadata else None,
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
                self.coordinator.transition_to_completed(state)
            elif status == ExecutionStatus.FAILED:
                self.coordinator.transition_to_failed(state, error or "Unknown error")
            
            # Save final state
            await self.state_store.save_state(state)