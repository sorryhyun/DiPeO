from typing import Any
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.enums import ContentType
from dipeo.core.execution.node_output import (
    NodeOutputProtocol,
    BaseNodeOutput,
    TextOutput,
    DataOutput,
    ConversationOutput,
    ConditionOutput,
    ErrorOutput
)

class EnvelopeAdapter:
    """Bridge between legacy dict outputs and envelopes"""
    
    @staticmethod
    def from_legacy_output(
        output: Any,
        node_id: str = "unknown",
        trace_id: str = ""
    ) -> list[Envelope]:
        """Convert various legacy output formats to envelopes"""
        
        # Handle NodeOutputProtocol objects
        if isinstance(output, NodeOutputProtocol):
            if hasattr(output, 'as_envelopes'):
                return output.as_envelopes()
            
            # Extract value from NodeOutputProtocol
            content = output.value
            
            # Handle ErrorOutput specially
            if isinstance(output, ErrorOutput):
                content = {"error": output.error, "error_type": output.error_type}
                return [EnvelopeFactory.json(content, produced_by=node_id, trace_id=trace_id)]
            
            # Handle ConditionOutput
            if isinstance(output, ConditionOutput):
                branch_id, branch_data = output.get_branch_output()
                envelope = EnvelopeAdapter._create_envelope(
                    branch_data, node_id, trace_id
                ).with_meta(branch_id=branch_id, condition_result=output.value)
                return [envelope]
            
            # Handle ConversationOutput
            if isinstance(output, ConversationOutput):
                # Convert messages to conversation state
                messages = output.value
                state = {
                    "messages": messages,
                    "last_message": messages[-1] if messages else None
                }
                return [EnvelopeFactory.conversation(state, produced_by=node_id, trace_id=trace_id)]
            
            return [EnvelopeAdapter._create_envelope(content, node_id, trace_id)]
        
        # Handle direct values
        return [EnvelopeAdapter._create_envelope(output, node_id, trace_id)]
    
    @staticmethod
    def _create_envelope(content: Any, node_id: str, trace_id: str) -> Envelope:
        """Create appropriate envelope based on content type"""
        
        if content is None:
            return EnvelopeFactory.text("", produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, str):
            return EnvelopeFactory.text(content, produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, (dict, list)):
            return EnvelopeFactory.json(content, produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, bytes):
            return Envelope(
                content_type=ContentType.GENERIC,
                body=content,
                produced_by=node_id,
                trace_id=trace_id
            )
        else:
            # Fallback: convert to string
            return EnvelopeFactory.text(str(content), produced_by=node_id, trace_id=trace_id)
    
    @staticmethod
    def to_legacy_input(envelope: Envelope) -> Any:
        """Convert envelope back to expected legacy format"""
        
        if envelope.content_type == ContentType.RAW_TEXT:
            return envelope.body
        elif envelope.content_type == ContentType.OBJECT:
            return envelope.body
        elif envelope.content_type == ContentType.CONVERSATION_STATE:
            # Return the raw conversation state
            return envelope.body
        elif envelope.content_type == ContentType.GENERIC:
            # Generic can be used for binary or other types
            return envelope.body
        else:
            return envelope.body
    
    @staticmethod
    def wrap_handler_output(
        handler_result: Any,
        node_id: str,
        trace_id: str
    ) -> NodeOutputProtocol:
        """Wrap handler result with envelope support"""
        
        if isinstance(handler_result, NodeOutputProtocol):
            # Enhance existing NodeOutputProtocol with envelope support
            if not hasattr(handler_result, 'as_envelopes'):
                envelopes = EnvelopeAdapter.from_legacy_output(
                    handler_result, node_id, trace_id
                )
                handler_result._envelopes = envelopes
            return handler_result
        
        # Create new BaseNodeOutput with envelopes
        envelopes = EnvelopeAdapter.from_legacy_output(
            handler_result, node_id, trace_id
        )
        
        # Create appropriate output type based on content
        from dipeo.diagram_generated import NodeID
        node_id_obj = NodeID(node_id)
        
        if isinstance(handler_result, str):
            output = TextOutput(value=handler_result, node_id=node_id_obj)
        elif isinstance(handler_result, dict):
            output = DataOutput(value=handler_result, node_id=node_id_obj)
        else:
            output = BaseNodeOutput(value=handler_result, node_id=node_id_obj)
        
        output._envelopes = envelopes
        return output