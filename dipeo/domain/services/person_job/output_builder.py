"""Domain service for building person job outputs."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from dipeo.models import (
    DomainDiagram,
    Message,
    Conversation,
)


@dataclass
class PersonJobResult:
    """Result of a person job execution."""
    content: str
    conversation_state: Optional[Conversation] = None
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    tool_outputs: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {"content": self.content}
        
        if self.conversation_state:
            result["conversation"] = {
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "tool_calls": msg.tool_calls,
                        "tool_call_id": msg.tool_call_id,
                    }
                    for msg in self.conversation_state.messages
                ],
                "metadata": self.conversation_state.metadata,
            }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        if self.usage:
            result["usage"] = self.usage
            
        if self.tool_outputs:
            result["tool_outputs"] = self.tool_outputs
            
        return result


class PersonJobOutputBuilder:
    """Service for building outputs from person job executions."""
    
    def build_output(
        self,
        content: str,
        messages: List[Message],
        person_label: str,
        needs_conversation: bool,
        usage: Optional[Dict[str, Any]] = None,
        tool_outputs: Optional[List[Dict[str, Any]]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> PersonJobResult:
        """Build the output for a person job execution.
        
        Business logic:
        - Include conversation state if needed based on diagram connections
        - Format messages with person label
        - Include usage statistics and tool outputs
        - Build appropriate metadata
        """
        metadata = {"person": person_label}
        if additional_metadata:
            metadata.update(additional_metadata)
        
        conversation_state = None
        if needs_conversation and messages:
            conversation_state = self._build_conversation_state(messages, person_label)
        
        return PersonJobResult(
            content=content,
            conversation_state=conversation_state,
            metadata=metadata,
            usage=usage,
            tool_outputs=tool_outputs,
        )
    
    def _build_conversation_state(
        self,
        messages: List[Message],
        person_label: str,
    ) -> Conversation:
        """Build a conversation state from messages."""
        # Messages are already in the correct format
        # Store person info in the Conversation's extra fields (allowed by model_config)
        return Conversation(
            messages=messages,
            metadata=None,  # We don't have the required fields for ConversationMetadata
            person=person_label,  # Extra field allowed by model_config
        )