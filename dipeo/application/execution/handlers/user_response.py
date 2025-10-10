from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.user_response_node import UserResponseNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(execution_context=EXECUTION_CONTEXT)
class UserResponseNodeHandler(TypedNodeHandler[UserResponseNode]):
    """Handler for interactive user input.

    Now uses envelope-based communication for clean input/output interfaces.
    """

    NODE_TYPE = NodeType.USER_RESPONSE

    def __init__(self):
        super().__init__()

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
        """Convert envelope inputs to context for user prompt.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        # Convert envelope inputs to text for context
        input_context = None
        if envelope_inputs:
            # Check for default input first
            if default_envelope := self.get_optional_input(envelope_inputs, "default"):
                try:
                    input_context = default_envelope.as_json()
                except ValueError:
                    input_context = default_envelope.as_text()
            else:
                # Collect all inputs
                input_data = {}
                for key, envelope in envelope_inputs.items():
                    try:
                        input_data[key] = envelope.as_json()
                    except ValueError:
                        input_data[key] = envelope.as_text()
                input_context = input_data

        return {"input_context": input_context}

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[UserResponseNode]) -> Any:
        """Execute user response interaction."""
        node = request.node
        context = request.context

        # Get input context from prepared inputs
        input_context = inputs.get("input_context")

        # Get execution context from ServiceRegistry
        exec_context = self._execution_context

        # Support both dict-based and object-based execution context
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

        # Return empty response when no handler available
        return {"response": "", "has_handler": False}

    def serialize_output(
        self, result: Any, request: ExecutionRequest[UserResponseNode]
    ) -> Envelope:
        """Serialize user response to envelope."""
        node = request.node
        trace_id = request.execution_id or ""

        response = result.get("response", "")
        has_handler = result.get("has_handler", False)

        if has_handler:
            # Create output envelope with response
            output_envelope = EnvelopeFactory.create(
                body=response, produced_by=node.id, trace_id=trace_id
            ).with_meta(user_response=response)
        else:
            # Return empty response when no handler available
            output_envelope = EnvelopeFactory.create(
                body="", produced_by=node.id, trace_id=trace_id
            ).with_meta(warning="No interactive handler available", user_response="")

        return output_envelope

    def post_execute(
        self, request: ExecutionRequest[UserResponseNode], output: Envelope
    ) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
