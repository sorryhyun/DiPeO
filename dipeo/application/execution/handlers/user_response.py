
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.generated_nodes import UserResponseNode, NodeType
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class UserResponseNodeHandler(TypedNodeHandler[UserResponseNode]):
    """Handler for interactive user input.
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    # Enable envelope mode
    _expects_envelopes = True
    
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

    async def execute_with_envelopes(
        self, 
        request: ExecutionRequest[UserResponseNode],
        inputs: dict[str, Envelope]
    ) -> Envelope:
        return await self._execute_user_response(request, inputs)
    
    async def _execute_user_response(
        self, 
        request: ExecutionRequest[UserResponseNode],
        envelope_inputs: dict[str, Envelope]
    ) -> Envelope:
        # Extract properties from request
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        
        # Convert envelope inputs to text for context
        input_context = None
        if envelope_inputs:
            # Check for default input first
            if default_envelope := self.get_optional_input(envelope_inputs, 'default'):
                try:
                    input_context = self.reader.as_json(default_envelope)
                except ValueError:
                    input_context = self.reader.as_text(default_envelope)
            else:
                # Collect all inputs
                input_data = {}
                for key, envelope in envelope_inputs.items():
                    try:
                        input_data[key] = self.reader.as_json(envelope)
                    except ValueError:
                        input_data[key] = self.reader.as_text(envelope)
                input_context = input_data
        
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

            # Create output envelope
            output_envelope = EnvelopeFactory.text(
                response,
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                user_response=response
            )
            
            return output_envelope
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
