from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import STATE_STORE
from dipeo.diagram_generated.enums import HookTriggerMode, NodeType
from dipeo.diagram_generated.unified_nodes.start_node import StartNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.domain.execution.context.execution_context import ExecutionContext


@register_handler
@requires_services(state_store=STATE_STORE)
class StartNodeHandler(TypedNodeHandler[StartNode]):
    """Handler for start nodes with envelope support."""

    NODE_TYPE = NodeType.START.value

    @property
    def node_class(self) -> type[StartNode]:
        return StartNode

    @property
    def schema(self) -> type[BaseModel]:
        return StartNode

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    def validate(self, request: ExecutionRequest[StartNode]) -> str | None:
        node = request.node

        if node.trigger_mode == HookTriggerMode.HOOK and not node.hook_event:
            return "Hook event must be specified when using hook trigger mode"

        return None

    async def pre_execute(self, request: ExecutionRequest[StartNode]) -> Envelope | None:
        node = request.node

        request.set_handler_state("trigger_mode", node.trigger_mode or HookTriggerMode.NONE)
        request.set_handler_state("hook_event", node.hook_event)
        request.set_handler_state("hook_filters", node.hook_filters)

        input_variables = {}
        execution_id = None
        if request.execution_id:
            execution_id = request.execution_id
        elif request.runtime and hasattr(request.runtime, "execution_id"):
            execution_id = request.runtime.execution_id

        state_store = request.get_optional_service(STATE_STORE)

        if execution_id and state_store:
            execution_state = await state_store.get_state(execution_id)
            if execution_state and execution_state.variables:
                input_variables = execution_state.variables

        request.set_handler_state("input_variables", input_variables)

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[StartNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
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
        node = request.node
        context = request.context

        input_variables = request.get_handler_state("input_variables", {})
        trigger_mode = request.get_handler_state("trigger_mode", HookTriggerMode.NONE)
        hook_event = request.get_handler_state("hook_event")

        combined_data = {**input_variables, **inputs}

        if trigger_mode == HookTriggerMode.NONE:
            if combined_data and "default" in combined_data:
                output_data = combined_data
                message = "Simple start point"
            else:
                output_data = {"default": combined_data if combined_data else {}}
                message = "Simple start point"

        elif trigger_mode == HookTriggerMode.MANUAL:
            output_data = {**combined_data, **(node.custom_data or {})}
            output_data = {"default": output_data}
            message = "Manual execution started"

        elif trigger_mode == HookTriggerMode.HOOK:
            hook_data = await self._get_hook_event_data(node, context, request.services)

            if hook_data:
                output_data = {**combined_data, **(node.custom_data or {}), **hook_data}
                output_data = {"default": output_data}
                message = f"Triggered by hook event: {hook_event}"
            else:
                output_data = {**combined_data, **(node.custom_data or {})}
                output_data = {"default": output_data}
                message = "Hook trigger mode but no event data available"
        else:
            output_data = {"default": combined_data if combined_data else {}}
            message = "Simple start point"

        return {"data": output_data, "message": message}

    def serialize_output(self, result: Any, request: ExecutionRequest[StartNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        output_data = result.get("data", {})
        message = result.get("message", "Simple start point")

        trigger_mode = request.get_handler_state("trigger_mode")
        output_envelope = EnvelopeFactory.create(
            body=output_data,  # Natural dict output - let factory auto-detect
            produced_by=node.id,
            trace_id=trace_id,
            meta={
                "trigger_mode": str(trigger_mode) if trigger_mode else "none",
                "message": message,
            },
        )

        return output_envelope

    async def _get_hook_event_data(
        self, node: StartNode, context: "ExecutionContext", services: dict[str, Any]
    ) -> dict[str, Any] | None:
        return None

    def post_execute(self, request: ExecutionRequest[StartNode], output: Envelope) -> Envelope:
        self.emit_token_outputs(request, output)
        return output
