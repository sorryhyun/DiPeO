from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.nodes.start_node import StartNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.diagram_generated import HookTriggerMode, NodeType, StartNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class StartNodeHandler(TypedNodeHandler[StartNode]):
    
    def __init__(self):
        pass

    @property
    def node_class(self) -> type[StartNode]:
        return StartNode
    
    @property
    def node_type(self) -> str:
        return NodeType.start.value

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    @property
    def requires_services(self) -> list[str]:
        """Services required for execution."""
        return ["state_store"]

    def validate(self, request: ExecutionRequest[StartNode]) -> Optional[str]:
        """Validate the start node configuration."""
        node = request.node
        
        # Validate hook configuration
        if node.trigger_mode == HookTriggerMode.hook:
            if not node.hook_event:
                return "Hook event must be specified when using hook trigger mode"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[StartNode]) -> NodeOutputProtocol:
        """Execute the start node."""
        node = request.node
        context = request.context
        # Store node configuration in metadata for debugging
        request.add_metadata("trigger_mode", node.trigger_mode)
        request.add_metadata("hook_event", node.hook_event)
        request.add_metadata("hook_filters", node.hook_filters)
        
        # Get input variables from execution state
        input_variables = {}
        
        # Try to get execution ID
        execution_id = None
        if request.execution_id:
            execution_id = request.execution_id
        elif request.runtime and hasattr(request.runtime, 'execution_id'):
            execution_id = request.runtime.execution_id
        
        if execution_id:
            # Try to get state store service
            state_store = request.services.get("state_store")
            if state_store:
                execution_state = await state_store.get_state(execution_id)
                if execution_state and execution_state.variables:
                    input_variables = execution_state.variables
        
        # Direct typed access to node properties
        trigger_mode = node.trigger_mode or HookTriggerMode.manual
        
        if trigger_mode == HookTriggerMode.manual:
            # Merge input variables with custom_data (custom_data takes precedence)
            output_data = {**input_variables, **(node.custom_data or {})}
            
            return DataOutput(
                value={"default": output_data},
                node_id=node.id,
                metadata={"message": "Manual execution started"}
            )
        
        elif trigger_mode == HookTriggerMode.hook:
            hook_data = await self._get_hook_event_data(node, context, request.services)
            
            if hook_data:
                # Merge all three: input variables, custom_data, and hook_data (in that order of precedence)
                output_data = {**input_variables, **(node.custom_data or {}), **hook_data}
                return DataOutput(
                    value={"default": output_data},
                    node_id=node.id,
                    metadata={"message": f"Triggered by hook event: {node.hook_event}"}
                )
            else:
                # Merge input variables with custom_data
                output_data = {**input_variables, **(node.custom_data or {})}
                return DataOutput(
                    value={"default": output_data},
                    node_id=node.id,
                    metadata={"message": "Hook trigger mode but no event data available"}
                )
    
    async def _get_hook_event_data(
        self,
        node: StartNode,
        context: "ExecutionContext",
        services: dict[str, Any]
    ) -> dict[str, Any] | None:
        # TODO: In a real implementation, hook event data should be provided
        # through infrastructure services (e.g., message queue, webhook receiver)
        # rather than execution variables
        
        # For now, return None to indicate no event data
        return None
    
    def post_execute(
        self,
        request: ExecutionRequest[StartNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log start node execution."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            print(f"[StartNode] Executed with trigger mode: {request.metadata.get('trigger_mode')}")
        
        return output