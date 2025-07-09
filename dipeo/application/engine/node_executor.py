"""Node executor for handling individual node execution.

This module extracts node execution logic from ExecutionEngine to provide
a focused, single-responsibility component for node-level execution.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage

if TYPE_CHECKING:
    from dipeo.application.execution.context import ApplicationExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.domain.services.execution.protocols import ExecutionObserver
    from dipeo.models import ExecutionState

    from .execution_controller import ExecutionController
    from .execution_view import LocalExecutionView, NodeView

log = logging.getLogger(__name__)


class NodeExecutor:
    """Handles individual node execution.
    
    Responsibilities:
    - Context creation for node execution
    - Handler invocation
    - Result processing
    - State updates
    - Observer notifications
    """
    
    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        observers: Optional[list["ExecutionObserver"]] = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
    
    async def execute_node(
        self,
        node_view: "NodeView",
        execution_view: "LocalExecutionView",
        controller: "ExecutionController",
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Optional[Any] = None
    ) -> None:
        """Execute a single node.
        
        This method handles:
        1. Context creation
        2. Input gathering
        3. Service injection
        4. Handler invocation
        5. Result processing
        6. State updates
        7. Observer notifications
        """
        # Track start time
        start_time = datetime.utcnow()
        
        # Notify observers
        for observer in self.observers:
            await observer.on_node_start(execution_id, node_view.id)
        
        try:
            # Create runtime context
            context = self._create_runtime_context(
                node_view, execution_id, options, execution_view, controller
            )
            
            # Get inputs
            inputs = node_view.get_active_inputs()
            
            # Get services
            services = self.service_registry.get_handler_services(
                node_view._handler_def.requires_services
            )
            services["diagram"] = execution_view.diagram
            services["execution_context"] = {
                "interactive_handler": interactive_handler
            }
            
            # Prepare node data
            node_data = node_view.data.copy() if node_view.data else {}
            if node_view.node.type == NodeType.person_job.value:
                node_data.setdefault("first_only_prompt", "")
                node_data.setdefault("max_iteration", 1)
            
            # Execute handler
            output = await node_view.handler(
                props=node_view._handler_def.node_schema.model_validate(node_data),
                context=context,
                inputs=inputs,
                services=services,
            )
            
            # Update state
            node_view.output = output
            node_view.exec_count += 1
            await controller.mark_executed(node_view.id, output, node_view.node.type)
            
            # Create NodeState with output and timing information
            end_time = datetime.utcnow()
            
            # Extract token usage from output metadata if available
            token_usage = None
            if output and output.metadata and "token_usage" in output.metadata:
                token_usage_data = output.metadata["token_usage"]
                if token_usage_data:
                    token_usage = TokenUsage(**token_usage_data)
            
            node_state = NodeState(
                status=NodeExecutionStatus.COMPLETED,
                started_at=start_time.isoformat(),
                ended_at=end_time.isoformat(),
                error=None,
                token_usage=token_usage,
                output=output
            )
            
            # Notify observers
            for observer in self.observers:
                await observer.on_node_complete(
                    execution_id, node_view.id, node_state
                )
                
        except Exception as e:
            # Notify observers
            for observer in self.observers:
                await observer.on_node_error(execution_id, node_view.id, str(e))
            raise
    
    def _create_runtime_context(
        self,
        node_view: "NodeView",
        execution_id: str,
        options: dict[str, Any],
        execution_view: "LocalExecutionView",
        controller: "ExecutionController"
    ) -> "ApplicationExecutionContext":
        """Create runtime context for node execution.
        
        Builds an ApplicationExecutionContext with:
        - Current execution state
        - Node outputs collected so far
        - Service registry reference
        - Execution metadata
        """
        from dipeo.application.execution.context import (
            ApplicationExecutionContext,
        )
        
        # Get execution state from controller's state adapter
        if not controller.state_adapter:
            raise ValueError("Controller must have a state adapter")
            
        execution_state = controller.state_adapter.execution_state
        
        # Create ApplicationExecutionContext with the existing state
        return ApplicationExecutionContext(
            execution_state=execution_state,
            service_registry=self.service_registry,
            current_node_id=node_view.id,
            executed_nodes=list(controller.state_adapter.get_executed_nodes()),
            exec_counts=controller.state_adapter.get_all_node_exec_counts(),
        )