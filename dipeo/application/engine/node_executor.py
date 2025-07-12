# Node executor for handling individual node execution

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage, DomainDiagram

if TYPE_CHECKING:
    from dipeo.application.execution.context import UnifiedExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.application.protocols import ExecutionObserver
    from dipeo.models import ExecutionState

    from .execution_controller import ExecutionController

log = logging.getLogger(__name__)


class NodeExecutor:
    # Handles individual node execution
    
    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        observers: Optional[list["ExecutionObserver"]] = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
    
    async def execute_node(
        self,
        node_id: str,
        diagram: "DomainDiagram",
        controller: "ExecutionController",
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Optional[Any] = None
    ) -> None:
        # Track start time
        start_time = datetime.utcnow()
        
        # Find the node in the diagram
        # First check if diagram has _executable_diagram with typed nodes
        if hasattr(diagram, '_executable_diagram') and diagram._executable_diagram:
            executable_diagram = diagram._executable_diagram
            node = next((n for n in executable_diagram.nodes if n.id == node_id), None)
        else:
            # Fallback to dictionary-based nodes
            node = next((n for n in diagram.nodes if n.id == node_id), None)
        
        if not node:
            raise ValueError(f"Node {node_id} not found in diagram")
        
        # Notify observers
        for observer in self.observers:
            await observer.on_node_start(execution_id, node_id)
        
        try:
            # Create runtime context
            context = self._create_runtime_context(
                node_id, execution_id, options, controller
            )
            
            # Get inputs using input resolution service
            input_resolution_service = self.service_registry.get('input_resolution_service')
            if not input_resolution_service:
                raise ValueError("InputResolutionService is required but not found")
            
            # Get current state for input resolution
            node_outputs = controller.state_adapter.get_all_node_outputs()
            node_exec_counts = controller.state_adapter.get_all_node_exec_counts()
            
            # Resolve inputs for this node
            inputs = input_resolution_service.resolve_inputs_for_node(
                node_id=node_id,
                node_type=node.type,
                diagram=diagram,
                node_outputs=node_outputs,
                node_exec_counts=node_exec_counts,
                node_memory_config=self._get_node_memory_config(node)
            )
            
            # Get handler from registry
            from dipeo.application import get_global_registry
            registry = get_global_registry()
            handler_def = registry.get(node.type)
            if not handler_def:
                raise ValueError(f"No handler for node type: {node.type}")
            
            # Get services
            log.debug(f"Getting services for handler: {handler_def.requires_services}")
            services = self.service_registry.get_handler_services(
                handler_def.requires_services
            )
            log.debug(f"Retrieved services: {list(services.keys())}")
            services["diagram"] = diagram
            services["execution_context"] = {
                "interactive_handler": interactive_handler
            }
            
            # All nodes are now typed nodes from StaticDiagramCompiler
            if not (hasattr(node, 'to_dict') and callable(getattr(node, 'to_dict'))):
                raise ValueError(f"Node {node_id} is not a typed node. All nodes must be strongly-typed.")
            
            node_data = node.to_dict()
            # Pass the typed node in services for compatibility during migration
            services["typed_node"] = node
            
            if node.type == NodeType.person_job.value:
                node_data.setdefault("first_only_prompt", "")
                node_data.setdefault("max_iteration", 1)
            
            # Execute handler
            output = await handler_def.handler(
                props=handler_def.node_schema.model_validate(node_data),
                context=context,
                inputs=inputs,
                services=services,
            )
            
            # Update state
            await controller.mark_executed(node_id, output, node.type)
            
            # Get the actual node state from the controller to check if it's RUNNING or COMPLETED
            actual_node_state = controller.state_adapter.execution_state.node_states.get(node_id)
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
                status=actual_status,  # Use actual status from controller
                started_at=start_time.isoformat(),
                ended_at=end_time.isoformat() if actual_status == NodeExecutionStatus.COMPLETED else None,
                error=None,
                token_usage=token_usage,
                output=output
            )
            
            # Notify observers
            for observer in self.observers:
                await observer.on_node_complete(
                    execution_id, node_id, node_state
                )
                
        except Exception as e:
            # Notify observers
            for observer in self.observers:
                await observer.on_node_error(execution_id, node_id, str(e))
            raise
    
    def _create_runtime_context(
        self,
        node_id: str,
        execution_id: str,
        options: dict[str, Any],
        controller: "ExecutionController"
    ) -> "UnifiedExecutionContext":
        from dipeo.application.execution.context import (
            UnifiedExecutionContext,
        )
        
        # Get execution state from controller's state adapter
        if not controller.state_adapter:
            raise ValueError("Controller must have a state adapter")
            
        execution_state = controller.state_adapter.execution_state
        
        # Create UnifiedExecutionContext with the existing state
        return UnifiedExecutionContext(
            execution_state=execution_state,
            service_registry=self.service_registry,
            current_node_id=node_id,
            executed_nodes=list(controller.state_adapter.get_executed_nodes()),
            exec_counts=controller.state_adapter.get_all_node_exec_counts(),
        )
    
    def _get_node_memory_config(self, node: Any) -> Optional[dict[str, Any]]:
        """Extract memory config from typed node."""
        if hasattr(node, 'memory_config'):
            return node.memory_config
        else:
            return None