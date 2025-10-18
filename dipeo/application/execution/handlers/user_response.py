from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.user_response_node import UserResponseNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory


@register_handler
@requires_services(execution_context=EXECUTION_CONTEXT)
class UserResponseNodeHandler(TypedNodeHandler[UserResponseNode]):
    """Handler for interactive user input."""

    NODE_TYPE = NodeType.USER_RESPONSE

    @property
    def node_class(self) -> type[UserResponseNode]:
        return UserResponseNode

    @property
    def node_type(self) -> str:
        return NodeType.USER_RESPONSE.value

    @property
    def schema(self) -> type[BaseModel]:
        return UserResponseNode

    @property
    def description(self) -> str:
        return "Interactive node that prompts for user input"

    async def prepare_inputs(
        self, request: ExecutionRequest[UserResponseNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to context for user prompt."""
        envelope_inputs = self.get_effective_inputs(request, inputs)

        input_context = None
        if envelope_inputs:
            if default_envelope := self.get_optional_input(envelope_inputs, "default"):
                try:
                    input_context = default_envelope.as_json()
                except ValueError:
                    input_context = default_envelope.as_text()
            else:
                input_data = {}
                for key, envelope in envelope_inputs.items():
                    try:
                        input_data[key] = envelope.as_json()
                    except ValueError:
                        input_data[key] = envelope.as_text()
                input_context = input_data

        return {"input_context": input_context}

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[UserResponseNode]) -> Any:
        node = request.node
        context = request.context
        input_context = inputs.get("input_context")
        exec_context = self._execution_context
        interactive_handler = None
        if exec_context:
            if isinstance(exec_context, dict):
                interactive_handler = exec_context.get("interactive_handler")
            elif hasattr(exec_context, "interactive_handler"):
                interactive_handler = exec_context.interactive_handler

        if interactive_handler:
            message = node.prompt
            if input_context:
                input_str = str(input_context)
                message = f"{message}\n\nContext: {input_str}"

            response = await interactive_handler(
                {
                    "type": "user_input_required",
                    "node_id": getattr(context, "current_node_id", "unknown"),
                    "prompt": message,
                    "timeout": node.timeout,
                }
            )

            return {"response": response, "has_handler": True}

        return {"response": "", "has_handler": False}

    def serialize_output(
        self, result: Any, request: ExecutionRequest[UserResponseNode]
    ) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        response = result.get("response", "")
        has_handler = result.get("has_handler", False)

        if has_handler:
            output_envelope = EnvelopeFactory.create(
                body=response, produced_by=node.id, trace_id=trace_id
            ).with_meta(user_response=response)
        else:
            output_envelope = EnvelopeFactory.create(
                body="", produced_by=node.id, trace_id=trace_id
            ).with_meta(warning="No interactive handler available", user_response="")

        return output_envelope

    def post_execute(
        self, request: ExecutionRequest[UserResponseNode], output: Envelope
    ) -> Envelope:
        self.emit_token_outputs(request, output)
        return output
