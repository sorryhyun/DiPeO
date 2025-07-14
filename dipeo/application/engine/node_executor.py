# Type-aware node executor that leverages strongly-typed nodes
# This replaces the legacy NodeExecutor with a fully typed implementation

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.input.typed_input_resolution import TypedInputResolutionService
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.models import NodeExecutionStatus, NodeID, NodeState, TokenUsage

if TYPE_CHECKING:
    from dipeo.application.execution import UnifiedExecutionContext
    from dipeo.application.execution.simple_execution import SimpleExecution
    from dipeo.application.execution.types import TypedNodeHandler
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.core.ports import ExecutionObserver
    from dipeo.models import NodeOutput

log = logging.getLogger(__name__)

class NodeExecutor:
    """Type-aware node executor that leverages typed nodes for better performance and safety.
    
    This is the primary node executor that works with strongly-typed nodes from the
    StaticDiagramCompiler for better performance and type safety.
    """
    
    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
    
    async def execute_node(
        self,
        node: ExecutableNode,
        execution: "SimpleExecution",
        handler: Optional["TypedNodeHandler"] = None,
        execution_id: str = "",
        options: dict[str, Any] | None = None,
        interactive_handler: Any | None = None
    ) -> None:
        """Execute a typed node with type-specific logic."""
        # Track start time
        start_time = datetime.utcnow()
        node_id_str = str(node.id)
        log.debug(f"NodeExecutor: Starting execution of node {node_id_str} (type: {node.type})")
        
        # Notify observers
        for observer in self.observers:
            await observer.on_node_start(execution_id, node_id_str)
        
        try:
            # Type-specific pre-execution logic
            pre_execution_data = await self._pre_execute_typed(node, execution)
            
            # Create runtime context
            context = self._create_typed_context(
                node=node,
                execution=execution,
                pre_execution_data=pre_execution_data,
                options=options or {}
            )
            
            # Get inputs using typed resolution
            inputs = await self._resolve_typed_inputs(node, execution)
            
            # Get handler if not provided
            if not handler:
                handler = await self._get_typed_handler(node)
            
            # Prepare services
            services = await self._prepare_typed_services(node, execution, handler)
            services["execution_context"] = {
                "interactive_handler": interactive_handler
            }
            
            # Execute handler with typed node directly
            output = await handler.execute(
                node=node,
                context=context,
                inputs=inputs,
                services=services,
            )
            
            # Update state with typed execution
            await self._update_typed_state(node, execution, output)
            
            # Get the actual node state
            actual_node_state = execution.get_node_state(node.id)
            actual_status = actual_node_state.status if actual_node_state else NodeExecutionStatus.COMPLETED
            
            # Create NodeState with output and timing information
            end_time = datetime.utcnow()
            
            # Extract token usage from output metadata if available
            token_usage = None
            if output and output.metadata and "token_usage" in output.metadata:
                token_usage_data = output.metadata["token_usage"]
                if token_usage_data:
                    token_usage = TokenUsage(**token_usage_data)
            
            node_state = NodeState(
                status=actual_status,
                started_at=start_time.isoformat(),
                ended_at=end_time.isoformat() if actual_status == NodeExecutionStatus.COMPLETED else None,
                error=None,
                token_usage=token_usage,
                output=output
            )
            
            # Notify observers
            for observer in self.observers:
                await observer.on_node_complete(
                    execution_id, node_id_str, node_state
                )
                
        except Exception as e:
            # Notify observers
            for observer in self.observers:
                await observer.on_node_error(execution_id, node_id_str, str(e))
            raise
    
    async def _pre_execute_typed(
        self, 
        node: ExecutableNode, 
        execution: "SimpleExecution"
    ) -> dict[str, Any]:
        """Type-specific pre-execution logic."""
        # Get the handler for this node type and call its pre_execute method
        handler = await self._get_typed_handler(node)
        return await handler.pre_execute(node, execution)
    
    def _create_typed_context(
        self,
        node: ExecutableNode,
        execution: "SimpleExecution",
        pre_execution_data: dict[str, Any],
        options: dict[str, Any]
    ) -> "UnifiedExecutionContext":
        """Get context from execution and update current node."""
        # Use the context from execution
        context = execution.context
        
        # Update current node
        context._current_node = node.id
        
        # Add pre-execution data to context
        context.pre_execution_data = pre_execution_data
        
        # Register diagram as a service for handlers
        context._service_registry.register("diagram", execution.diagram)
        
        return context
    
    async def _resolve_typed_inputs(
        self,
        node: ExecutableNode,
        execution: "SimpleExecution"
    ) -> dict[str, Any]:
        """Resolve inputs using typed node information."""
        # Use context's resolve_inputs method
        return execution.context.resolve_inputs(node, execution.diagram)
    
    def _get_typed_memory_config(self, node: ExecutableNode) -> dict[str, Any] | None:
        """Extract memory config from typed node."""
        if isinstance(node, PersonJobNode) and node.memory_config:
            return node.memory_config
        return None
    
    async def _get_typed_handler(self, node: ExecutableNode) -> "TypedNodeHandler":
        """Get handler for typed node."""
        from dipeo.application import get_global_registry
        from dipeo.application.execution.handler_factory import HandlerFactory
        
        registry = get_global_registry()
        
        # Ensure service registry is set
        if not hasattr(registry, '_service_registry') or registry._service_registry is None:
            # Create HandlerFactory to initialize the global registry with service registry
            HandlerFactory(self.service_registry)
        
        # Since handlers are now TypedNodeHandler instances,
        # we can use create_handler to get the instance
        return registry.create_handler(node.type)
    
    async def _prepare_typed_services(
        self,
        node: ExecutableNode,
        execution: "SimpleExecution",
        handler: "TypedNodeHandler"
    ) -> dict[str, Any]:
        """Prepare services with typed node information."""
        # Get required services
        services = self.service_registry.get_handler_services(
            handler.requires_services
        )
        
        # Add diagram from execution
        services["diagram"] = execution.diagram
        
        return services
    
    async def _update_typed_state(
        self,
        node: ExecutableNode,
        execution: "SimpleExecution",
        output: "NodeOutput"
    ) -> None:
        """Update execution state using typed node information."""
        # Type-specific state updates
        if isinstance(node, PersonJobNode):
            exec_count = execution.context.get_node_execution_count(node.id)
            
            # Check if max iterations reached
            if exec_count >= node.max_iteration:
                # Check if output indicates max iteration was hit
                if output and output.metadata and output.metadata.get("skipped") and "Max iteration" in output.metadata.get("reason", ""):
                    execution.set_node_state(node.id, NodeExecutionStatus.MAXITER_REACHED)
                else:
                    execution.context.complete_node(node.id, output)
            else:
                # Not at max iteration yet, mark as complete then reset to pending
                execution.context.complete_node(node.id, output)
                execution.context.reset_node(node.id)
        else:
            # For non-PersonJobNode types, just mark as complete
            execution.context.complete_node(node.id, output)