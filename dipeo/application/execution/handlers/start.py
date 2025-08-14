import json
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import StartNode, NodeType
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.start_model import StartNodeData, HookTriggerMode
from dipeo.application.registry import STATE_STORE

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class StartNodeHandler(TypedNodeHandler[StartNode]):
    """Handler for start nodes with envelope support."""
    
    # Enable envelope mode
    _expects_envelopes = True
    
    def __init__(self):
        super().__init__()
        # Instance variables for passing data between methods
        self._current_trigger_mode = None
        self._current_hook_event = None
        self._current_hook_filters = None
        self._current_state_store = None
        self._current_input_variables = None

    @property
    def node_class(self) -> type[StartNode]:
        return StartNode
    
    @property
    def node_type(self) -> str:
        return NodeType.START.value

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    @property
    def requires_services(self) -> list[str]:
        return ["state_store"]

    def validate(self, request: ExecutionRequest[StartNode]) -> Optional[str]:
        """Static validation - structural checks only"""
        node = request.node
        
        if node.trigger_mode == HookTriggerMode.HOOK:
            if not node.hook_event:
                return "Hook event must be specified when using hook trigger mode"
        
        return None
    
    async def pre_execute(self, request: ExecutionRequest[StartNode]) -> Optional[Envelope]:
        """Runtime validation and setup"""
        node = request.node
        
        # Extract configuration
        self._current_trigger_mode = node.trigger_mode or HookTriggerMode.NONE
        self._current_hook_event = node.hook_event
        self._current_hook_filters = node.hook_filters
        
        # Get state store service
        self._current_state_store = request.services.resolve(STATE_STORE)
        
        # Get input variables from execution state
        self._current_input_variables = {}
        execution_id = None
        if request.execution_id:
            execution_id = request.execution_id
        elif request.runtime and hasattr(request.runtime, 'execution_id'):
            execution_id = request.runtime.execution_id
        
        if execution_id and self._current_state_store:
            execution_state = await self._current_state_store.get_state(execution_id)
            if execution_state and execution_state.variables:
                self._current_input_variables = execution_state.variables
        
        return None
    
    async def execute_with_envelopes(
        self,
        request: ExecutionRequest[StartNode],
        inputs: dict[str, Envelope]
    ) -> Envelope:
        """Execute start node with envelope inputs."""
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        
        # Process any incoming envelopes (though Start nodes typically don't have inputs)
        input_data = {}
        for key, envelope in inputs.items():
            if envelope.content_type == "raw_text":
                input_data[key] = self.reader.as_text(envelope)
            elif envelope.content_type == "object":
                input_data[key] = self.reader.as_json(envelope)
            else:
                input_data[key] = envelope.body
        
        # Merge with input variables
        combined_data = {**self._current_input_variables, **input_data}
        
        # Determine output based on trigger mode
        if self._current_trigger_mode == HookTriggerMode.NONE:
            if combined_data and 'default' in combined_data:
                output_data = combined_data
                message = "Simple start point"
            else:
                output_data = {"default": combined_data if combined_data else {}}
                message = "Simple start point"
        
        elif self._current_trigger_mode == HookTriggerMode.MANUAL:
            output_data = {**combined_data, **(node.custom_data or {})}
            output_data = {"default": output_data}
            message = "Manual execution started"
        
        elif self._current_trigger_mode == HookTriggerMode.HOOK:
            hook_data = await self._get_hook_event_data(node, context, request.services)
            
            if hook_data:
                output_data = {**combined_data, **(node.custom_data or {}), **hook_data}
                output_data = {"default": output_data}
                message = f"Triggered by hook event: {self._current_hook_event}"
            else:
                output_data = {**combined_data, **(node.custom_data or {})}
                output_data = {"default": output_data}
                message = "Hook trigger mode but no event data available"
        
        # Create envelope output
        output_envelope = EnvelopeFactory.json(
            output_data,
            produced_by=node.id,
            trace_id=trace_id
        ).with_meta(
            trigger_mode=str(self._current_trigger_mode) if self._current_trigger_mode else "none",
            message=message
        )
        
        return output_envelope
    
    async def _get_hook_event_data(
        self,
        node: StartNode,
        context: "ExecutionContext",
        services: dict[str, Any]
    ) -> dict[str, Any] | None:
        # TODO: Hook event data should be provided through infrastructure services
        return None
    
    def post_execute(
        self,
        request: ExecutionRequest[StartNode],
        output: Envelope
    ) -> Envelope:
        # Debug logging without using request.metadata
        if self._current_trigger_mode:
            print(f"[StartNode] Executed with trigger mode: {self._current_trigger_mode}")
        
        return output