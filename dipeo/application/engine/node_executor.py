# Type-aware node executor that leverages strongly-typed nodes
# This replaces the legacy NodeExecutor with a fully typed implementation

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage, NodeID
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.application.execution.input.typed_input_resolution import TypedInputResolutionService
from dipeo.core.static.generated_nodes import PersonJobNode

if TYPE_CHECKING:
    from dipeo.application.execution.context import UnifiedExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.core.ports import ExecutionObserver
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
    from dipeo.application.execution.types import TypedNodeHandler
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
        observers: Optional[List["ExecutionObserver"]] = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
    
    async def execute_node(
        self,
        node: ExecutableNode,
        execution: "TypedStatefulExecution",
        handler: Optional["TypedNodeHandler"] = None,
        execution_id: str = "",
        options: Optional[Dict[str, Any]] = None,
        interactive_handler: Optional[Any] = None
    ) -> None:
        """Execute a typed node with type-specific logic."""
        # Track start time
        start_time = datetime.utcnow()
        node_id_str = str(node.id)
        
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
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Type-specific pre-execution logic."""
        # Get the handler for this node type and call its pre_execute method
        handler = await self._get_typed_handler(node)
        return await handler.pre_execute(node, execution)
    
    def _create_typed_context(
        self,
        node: ExecutableNode,
        execution: "TypedStatefulExecution",
        pre_execution_data: Dict[str, Any],
        options: Dict[str, Any]
    ) -> "UnifiedExecutionContext":
        """Create context with typed node information."""
        from dipeo.application.execution.context import UnifiedExecutionContext
        
        # Create context with typed execution state
        context = UnifiedExecutionContext(
            execution_state=execution.state,
            service_registry=self.service_registry,
            current_node_id=str(node.id),
            executed_nodes=execution.executed_nodes,
            exec_counts={
                str(node_id): execution.get_node_execution_count(NodeID(node_id))
                for node_id in execution.state.node_states
            },
        )
        
        # Add pre-execution data to context
        context.pre_execution_data = pre_execution_data
        
        return context
    
    async def _resolve_typed_inputs(
        self,
        node: ExecutableNode,
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Resolve inputs using typed node information."""
        
        # Create typed input resolution service
        typed_input_service = TypedInputResolutionService()
        
        # Get current state for input resolution
        node_outputs = execution.state.node_outputs
        node_exec_counts = {
            str(node_id): execution.get_node_execution_count(NodeID(node_id))
            for node_id in execution.state.node_states
        }
        
        # Resolve inputs using the typed ExecutableDiagram
        inputs = typed_input_service.resolve_inputs_for_node(
            node_id=str(node.id),
            node_type=node.type,
            diagram=execution.diagram,  # Use ExecutableDiagram directly
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts,
            node_memory_config=self._get_typed_memory_config(node)
        )
        
        return inputs
    
    def _get_typed_memory_config(self, node: ExecutableNode) -> Optional[Dict[str, Any]]:
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
        execution: "TypedStatefulExecution",
        handler: "TypedNodeHandler"
    ) -> Dict[str, Any]:
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
        execution: "TypedStatefulExecution",
        output: "NodeOutput"
    ) -> None:
        """Update execution state using typed node information."""
        # Mark node as complete
        execution.mark_node_complete(node.id)
        
        # Store output
        if output:
            execution.set_node_output(node.id, output)
        
        # Type-specific state updates
        if isinstance(node, PersonJobNode):
            # Check if we should reset to pending for iteration
            exec_count = execution.get_node_execution_count(node.id)
            if exec_count < node.max_iteration:
                # Reset to pending for next iteration
                execution.set_node_state(node.id, NodeExecutionStatus.PENDING)