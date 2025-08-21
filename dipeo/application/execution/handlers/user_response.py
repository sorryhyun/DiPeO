
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.generated_nodes import UserResponseNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext


@register_handler
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
        return UserResponseNodeData
    

    @property
    def description(self) -> str:
        return "Interactive node that prompts for user input"

    async def prepare_inputs(
        self,
        request: ExecutionRequest[UserResponseNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to context for user prompt."""
        # Convert envelope inputs to text for context
        input_context = None
        if inputs:
            # Check for default input first
            if default_envelope := self.get_optional_input(inputs, 'default'):
                try:
                    input_context = default_envelope.as_json()
                except ValueError:
                    input_context = default_envelope.as_text()
            else:
                # Collect all inputs
                input_data = {}
                for key, envelope in inputs.items():
                    try:
                        input_data[key] = envelope.as_json()
                    except ValueError:
                        input_data[key] = envelope.as_text()
                input_context = input_data
        
        return {"input_context": input_context}
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[UserResponseNode]
    ) -> Any:
        """Execute user response interaction."""
        node = request.node
        context = request.context
        
        # Get input context from prepared inputs
        input_context = inputs.get("input_context")
        
        # Get execution context from ServiceRegistry
        exec_context = request.services.resolve(EXECUTION_CONTEXT)
        if (
            exec_context
            and hasattr(exec_context, "interactive_handler")
            and exec_context.interactive_handler
        ):
            message = node.prompt
            if input_context:
                input_str = str(input_context)
                message = f"{message}\n\nContext: {input_str}"

            response = await exec_context.interactive_handler(
                {
                    "type": "user_input_required",
                    "node_id": getattr(context, 'current_node_id', 'unknown'),
                    "prompt": message,
                    "timeout": node.timeout,
                }
            )

            return {"response": response, "has_handler": True}
        
        # Return empty response when no handler available
        return {"response": "", "has_handler": False}
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[UserResponseNode]
    ) -> Envelope:
        """Serialize user response to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        response = result.get("response", "")
        has_handler = result.get("has_handler", False)
        
        if has_handler:
            # Create output envelope with response
            output_envelope = EnvelopeFactory.text(
                response,
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                user_response=response
            )
        else:
            # Return empty response when no handler available
            output_envelope = EnvelopeFactory.text(
                "",
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                warning="No interactive handler available",
                user_response=""
            )
        
        return output_envelope
