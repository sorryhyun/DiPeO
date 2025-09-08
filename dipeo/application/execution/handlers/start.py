from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry import STATE_STORE
from dipeo.diagram_generated.enums import HookTriggerMode, NodeType
from dipeo.diagram_generated.unified_nodes.start_node import StartNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext


@register_handler
class StartNodeHandler(TypedNodeHandler[StartNode]):
    """Handler for start nodes with envelope support."""

    NODE_TYPE = NodeType.START.value

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
    def schema(self) -> type[BaseModel]:
        return StartNode

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    @property
    def requires_services(self) -> list[str]:
        return ["state_store"]

    def validate(self, request: ExecutionRequest[StartNode]) -> str | None:
        """Static validation - structural checks only"""
        node = request.node

        if node.trigger_mode == HookTriggerMode.HOOK and not node.hook_event:
            return "Hook event must be specified when using hook trigger mode"

        return None

    async def pre_execute(self, request: ExecutionRequest[StartNode]) -> Envelope | None:
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
        elif request.runtime and hasattr(request.runtime, "execution_id"):
            execution_id = request.runtime.execution_id

        if execution_id and self._current_state_store:
            execution_state = await self._current_state_store.get_state(execution_id)
            if execution_state and execution_state.variables:
                self._current_input_variables = execution_state.variables

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[StartNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data for start node."""
        # Process any incoming envelopes (though Start nodes typically don't have inputs)
        input_data = {}
        for key, envelope in inputs.items():
            if envelope.content_type == "raw_text":
                input_data[key] = envelope.as_text()
            elif envelope.content_type == "object":
                input_data[key] = envelope.as_json()
            else:
                input_data[key] = envelope.body

        return input_data

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[StartNode]) -> Any:
        """Execute start node logic."""
        node = request.node
        context = request.context

        # Don't start a new epoch here - epoch 0 is the initial epoch
        # context.begin_epoch()  # REMOVED - this was causing epoch mismatch

        # Merge with input variables
        combined_data = {**self._current_input_variables, **inputs}

        # Determine output based on trigger mode
        if self._current_trigger_mode == HookTriggerMode.NONE:
            if combined_data and "default" in combined_data:
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
        else:
            # Default case
            output_data = {"default": combined_data if combined_data else {}}
            message = "Simple start point"

        # Return data with metadata for serialization
        return {"data": output_data, "message": message}

    def serialize_output(self, result: Any, request: ExecutionRequest[StartNode]) -> Envelope:
        """Serialize start node result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""

        # Extract data and message from result
        output_data = result.get("data", {})
        message = result.get("message", "Simple start point")

        # Create envelope with natural data output - auto-detect content type
        output_envelope = EnvelopeFactory.create(
            body=output_data,  # Natural dict output - let factory auto-detect
            produced_by=node.id,
            trace_id=trace_id,
            meta={
                "trigger_mode": str(self._current_trigger_mode)
                if self._current_trigger_mode
                else "none",
                "message": message,
            },
        )

        return output_envelope

    async def _get_hook_event_data(
        self, node: StartNode, context: "ExecutionContext", services: dict[str, Any]
    ) -> dict[str, Any] | None:
        # TODO: Hook event data should be provided through infrastructure services
        return None

    def post_execute(self, request: ExecutionRequest[StartNode], output: Envelope) -> Envelope:
        # Debug logging without using request.metadata
        # Emit output as tokens to trigger downstream nodes
        context = request.context
        outputs = {"default": output}
        context.emit_outputs_as_tokens(request.node.id, outputs)

        return output
