# Type-aware node executor that leverages strongly-typed nodes
# This replaces the legacy NodeExecutor with a fully typed implementation

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage, NodeID
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.application.execution.input.typed_input_resolution import TypedInputResolutionService
from dipeo.core.static.generated_nodes import (
    PersonJobNode, ConditionNode, StartNode, EndpointNode,
    CodeJobNode, ApiJobNode, DBNode, HookNode, UserResponseNode, NotionNode
)

if TYPE_CHECKING:
    from dipeo.application.execution.context import UnifiedExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.application.protocols import ExecutionObserver
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
    from dipeo.application.execution.typed_handler_base import TypedNodeHandler
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
        
        # Type-specific pre-execution handlers
        self.pre_execution_handlers = {
            PersonJobNode: self._pre_execute_person_job,
            EndpointNode: self._pre_execute_endpoint,
            CodeJobNode: self._pre_execute_code_job,
            ApiJobNode: self._pre_execute_api_job,
            ConditionNode: self._pre_execute_condition,
            DBNode: self._pre_execute_db,
            HookNode: self._pre_execute_hook,
            StartNode: self._pre_execute_start,
            UserResponseNode: self._pre_execute_user_response,
            NotionNode: self._pre_execute_notion
        }
    
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
            
            # Prepare services with typed node
            services = await self._prepare_typed_services(node, execution, handler)
            services["typed_node"] = node
            services["execution_context"] = {
                "interactive_handler": interactive_handler
            }
            
            # Execute handler with typed data
            node_data = node.to_dict()
            
            # Add type-specific defaults
            if isinstance(node, PersonJobNode):
                node_data.setdefault("first_only_prompt", "")
                node_data.setdefault("max_iteration", 1)
            
            output = await handler.execute(
                props=handler.schema.model_validate(node_data),
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
        # Get the handler for this node type
        handler = self.pre_execution_handlers.get(type(node))
        if handler:
            return await handler(node, execution)
        return {}
    
    async def _pre_execute_person_job(
        self, 
        node: PersonJobNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for PersonJobNode."""
        exec_count = execution.get_node_execution_count(node.id)
        
        # Determine which prompt to use
        if exec_count == 0 and node.first_only_prompt:
            prompt = node.first_only_prompt
        else:
            prompt = node.default_prompt
        
        return {
            "prompt": prompt,
            "exec_count": exec_count,
            "should_continue": exec_count < node.max_iteration,
            "memory_config": node.memory_config,
            "tools": node.tools
        }
    
    async def _pre_execute_endpoint(
        self, 
        node: EndpointNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for EndpointNode."""
        save_config = None
        if node.save_to_file:
            save_config = {
                "save": True,
                "filename": node.file_name or f"output_{node.id}.json"
            }
        
        return {"save_config": save_config}
    
    async def _pre_execute_code_job(
        self, 
        node: CodeJobNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for CodeJobNode."""
        return {
            "language": node.language.value if hasattr(node.language, 'value') else node.language,
            "code": node.code,
            "timeout": node.timeout
        }
    
    async def _pre_execute_api_job(
        self, 
        node: ApiJobNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for ApiJobNode."""
        return {
            "url": node.url,
            "method": node.method.value if hasattr(node.method, 'value') else node.method,
            "headers": node.headers,
            "params": node.params,
            "body": node.body,
            "timeout": node.timeout,
            "auth_type": node.auth_type,
            "auth_config": node.auth_config
        }
    
    async def _pre_execute_condition(
        self, 
        node: ConditionNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for ConditionNode."""
        return {
            "condition_type": node.condition_type,
            "expression": node.expression,
            "node_indices": node.node_indices
        }
    
    async def _pre_execute_db(
        self, 
        node: DBNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for DBNode."""
        return {
            "file": node.file,
            "collection": node.collection,
            "sub_type": node.sub_type.value if hasattr(node.sub_type, 'value') else node.sub_type,
            "operation": node.operation,
            "query": node.query,
            "data": node.data
        }
    
    async def _pre_execute_hook(
        self, 
        node: HookNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for HookNode."""
        return {}
    
    async def _pre_execute_start(
        self, 
        node: StartNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for StartNode."""
        return {
            "custom_data": node.custom_data,
            "output_data_structure": node.output_data_structure,
            "trigger_mode": node.trigger_mode,
            "hook_event": node.hook_event,
            "hook_filters": node.hook_filters
        }
    
    async def _pre_execute_user_response(
        self, 
        node: UserResponseNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for UserResponseNode."""
        return {
            "prompt": node.prompt,
            "timeout": node.timeout
        }
    
    async def _pre_execute_notion(
        self, 
        node: NotionNode, 
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execute logic for NotionNode."""
        return {
            "operation": node.operation.value if hasattr(node.operation, 'value') else node.operation,
            "page_id": node.page_id,
            "database_id": node.database_id
        }
    
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
        # Get arrow processor for the typed input resolution
        arrow_processor = self.service_registry.get('arrow_processor')
        if not arrow_processor:
            # Fallback to empty inputs if no arrow processor
            return {}
        
        # Create typed input resolution service
        typed_input_service = TypedInputResolutionService(arrow_processor)
        
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
            execution.set_node_output(node.id, output.value)
        
        # Type-specific state updates
        if isinstance(node, PersonJobNode):
            # Check if we should reset to pending for iteration
            exec_count = execution.get_node_execution_count(node.id)
            if exec_count < node.max_iteration:
                # Reset to pending for next iteration
                execution.set_node_state(node.id, NodeExecutionStatus.PENDING)