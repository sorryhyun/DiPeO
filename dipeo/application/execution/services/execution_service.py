"""Simplified execution service that delegates to use cases."""

from typing import TYPE_CHECKING, Any, Dict, Optional
from collections.abc import AsyncGenerator

from dipeo.core import BaseService

if TYPE_CHECKING:
    from dipeo.infra.persistence.diagram import DiagramStorageAdapter
    from ...unified_service_registry import UnifiedServiceRegistry
    from ..use_cases import ExecuteDiagramUseCase
    from dipeo.core.ports import ExecutionContextPort, StateStorePort, MessageRouterPort
    from dipeo.models import NodeOutput

class ExecutionService(BaseService):
    """Application service for execution operations.
    
    This service acts as a facade, delegating to appropriate use cases
    for diagram and node execution while handling cross-cutting concerns
    like monitoring and persistence coordination.
    """

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
        
        # Create use case instances
        self._diagram_use_case: Optional["ExecuteDiagramUseCase"] = None

    async def initialize(self):
        """Initialize the service and its use cases."""
        # Create use cases
        from ..use_cases import ExecuteDiagramUseCase
        
        self._diagram_use_case = ExecuteDiagramUseCase(
            service_registry=self.service_registry,
            state_store=self.state_store,
            message_router=self.message_router,
            diagram_storage_service=self.diagram_storage_service,
        )
        
        # Initialize use cases
        await self._diagram_use_case.initialize()

    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Any] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a complete diagram.
        
        Delegates to ExecuteDiagramUseCase for the actual execution logic.
        """
        if not self._diagram_use_case:
            raise RuntimeError("Service not initialized. Call initialize() first.")
        
        # Delegate to use case
        async for update in self._diagram_use_case.execute_diagram(
            diagram=diagram,
            options=options,
            execution_id=execution_id,
            interactive_handler=interactive_handler,
        ):
            yield update


    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an execution."""
        state = await self.state_store.get_state(execution_id)
        if state:
            return {
                "id": state.id,
                "status": state.status,
                "started_at": state.started_at,
                "completed_at": state.completed_at,
                "error": state.error,
                "node_states": state.node_states,
                "is_active": state.is_active,
            }
        return None

    async def list_executions(self, limit: int = 10) -> list[Dict[str, Any]]:
        """List recent executions."""
        # This would typically query a persistence layer
        # For now, return empty list as placeholder
        return []

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        state = await self.state_store.get_state(execution_id)
        if state and state.is_active:
            # Update state to cancelled
            from dipeo.models import ExecutionStatus
            from dipeo.domain.services.execution.state_machine import ExecutionStateMachine
            
            ExecutionStateMachine.transition_to_cancelled(state)
            await self.state_store.save_state(state)
            
            # Send cancellation message
            await self.message_router.publish_message(
                channel=f"execution/{execution_id}",
                message={
                    "type": "execution_cancelled",
                    "execution_id": execution_id,
                }
            )
            return True
        return False