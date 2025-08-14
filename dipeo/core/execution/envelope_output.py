"""EnvelopeOutput adapter for seamless migration from NodeOutput to Envelope.

This module provides adapter classes that wrap Envelope instances to provide
full NodeOutputProtocol compatibility during the migration period.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
from datetime import datetime
import json

from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    from dipeo.diagram_generated import NodeID, TokenUsage, Status, Message


class EnvelopeOutput:
    """Adapter that wraps an Envelope to provide NodeOutputProtocol interface.
    
    This class bridges the gap between the new Envelope system and the legacy
    NodeOutput system, allowing gradual migration of handlers.
    """
    
    def __init__(self, envelope: Envelope | None = None, **kwargs):
        """Initialize with an envelope or create one from kwargs.
        
        Args:
            envelope: Pre-existing envelope to wrap
            **kwargs: Arguments to create a new envelope if none provided
        """
        if envelope is None:
            # Create envelope from kwargs for convenience
            body = kwargs.pop("value", kwargs.pop("body", None))
            node_id = kwargs.pop("node_id", None)
            content_type = kwargs.pop("content_type", ContentType.RAW_TEXT)
            meta = kwargs.pop("meta", {})
            
            # Add common metadata
            if "timestamp" not in meta:
                meta["timestamp"] = datetime.now().timestamp()
            
            envelope = Envelope(
                body=body,
                produced_by=str(node_id) if node_id else "system",
                content_type=content_type,
                meta=meta,
                **kwargs
            )
        
        self._envelope = envelope
    
    # Delegate all NodeOutputProtocol properties to the envelope
    @property
    def value(self) -> Any:
        return self._envelope.value
    
    @property
    def node_id(self) -> 'NodeID':
        return self._envelope.node_id
    
    @property
    def metadata(self) -> str:
        return self._envelope.metadata
    
    @property
    def timestamp(self) -> datetime:
        return self._envelope.timestamp
    
    @property
    def token_usage(self) -> 'TokenUsage | None':
        return self._envelope.token_usage
    
    @property
    def execution_time(self) -> float | None:
        return self._envelope.execution_time
    
    @property
    def retry_count(self) -> int:
        return self._envelope.retry_count
    
    @property
    def status(self) -> 'Status | None':
        return self._envelope.status
    
    @property
    def error(self) -> str | None:
        return self._envelope.error
    
    def get_output(self, key: str, default: Any = None) -> Any:
        return self._envelope.get_output(key, default)
    
    def has_error(self) -> bool:
        return self._envelope.has_error()
    
    def to_dict(self) -> dict[str, Any]:
        return self._envelope.to_dict()
    
    def get_metadata_dict(self) -> dict[str, Any]:
        return self._envelope.get_metadata_dict()
    
    def set_metadata_dict(self, data: dict[str, Any]) -> None:
        # Since envelope is immutable, we need to create a new one
        new_meta = {**self._envelope.meta, **data}
        self._envelope = self._envelope.with_meta(**new_meta)
    
    def as_envelopes(self) -> list[Envelope]:
        return [self._envelope]
    
    def primary_envelope(self) -> Envelope:
        return self._envelope
    
    @classmethod
    def text(cls, content: str, node_id: str, **kwargs) -> 'EnvelopeOutput':
        """Create text output."""
        envelope = EnvelopeFactory.text(content, node_id=node_id, **kwargs)
        return cls(envelope)
    
    @classmethod
    def json(cls, data: Any, node_id: str, **kwargs) -> 'EnvelopeOutput':
        """Create JSON/object output."""
        envelope = EnvelopeFactory.json(data, node_id=node_id, **kwargs)
        return cls(envelope)
    
    @classmethod
    def error(cls, error_msg: str, node_id: str, error_type: str = "ExecutionError", **kwargs) -> 'EnvelopeOutput':
        """Create error output."""
        envelope = EnvelopeFactory.error(error_msg, error_type=error_type, node_id=node_id, **kwargs)
        return cls(envelope)
    


class ConversationEnvelopeOutput(EnvelopeOutput):
    """Specialized envelope output for conversation/person job nodes."""
    
    def __init__(self, messages: list['Message'], node_id: str, **kwargs):
        """Initialize with conversation messages.
        
        Args:
            messages: List of conversation messages
            node_id: ID of the producing node
            **kwargs: Additional metadata (person_id, model, token_usage, etc.)
        """
        # Extract specialized fields for metadata
        meta = kwargs.pop("meta", {})
        
        # Add person job specific metadata
        if "person_id" in kwargs:
            meta["person_id"] = kwargs.pop("person_id")
        if "conversation_id" in kwargs:
            meta["conversation_id"] = kwargs.pop("conversation_id")
        if "model" in kwargs:
            meta["model"] = kwargs.pop("model")
        if "token_usage" in kwargs:
            meta["token_usage"] = kwargs.pop("token_usage")
        
        # Create conversation state
        conversation_state = {
            "messages": messages,
            "last_message": messages[-1] if messages else None
        }
        
        envelope = EnvelopeFactory.conversation(
            conversation_state,
            node_id=node_id,
            meta=meta,
            **kwargs
        )
        
        super().__init__(envelope)
    
    def get_last_message(self) -> 'Message | None':
        """Get the last message in the conversation."""
        if isinstance(self._envelope.body, dict):
            return self._envelope.body.get("last_message")
        return None
    
    def get_messages_by_role(self, role: str) -> list['Message']:
        """Get messages filtered by role."""
        if isinstance(self._envelope.body, dict) and "messages" in self._envelope.body:
            messages = self._envelope.body["messages"]
            return [msg for msg in messages if hasattr(msg, 'role') and msg.role == role]
        return []


class ConditionEnvelopeOutput(EnvelopeOutput):
    """Specialized envelope output for condition nodes."""
    
    def __init__(self, condition_result: bool, node_id: str, 
                 true_output: Any = None, false_output: Any = None, **kwargs):
        """Initialize with condition result and branch outputs.
        
        Args:
            condition_result: Boolean result of the condition
            node_id: ID of the producing node
            true_output: Data for true branch
            false_output: Data for false branch
            **kwargs: Additional metadata
        """
        meta = kwargs.pop("meta", {})
        
        # Add condition-specific metadata
        meta["condtrue"] = true_output
        meta["condfalse"] = false_output
        meta["active_branch"] = "condtrue" if condition_result else "condfalse"
        
        envelope = Envelope(
            content_type=ContentType.OBJECT,
            body=condition_result,
            produced_by=node_id,
            meta=meta,
            **kwargs
        )
        
        super().__init__(envelope)
    
    def get_branch_output(self) -> tuple[str, Any]:
        """Get the active branch and its output."""
        branch = self._envelope.meta.get("active_branch", "condfalse")
        output = self._envelope.meta.get(branch)
        return (branch, output)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Override to handle condition-specific keys."""
        if key in ["condtrue", "condfalse", "active_branch"]:
            return self._envelope.meta.get(key, default)
        return super().get_output(key, default)


class DataEnvelopeOutput(EnvelopeOutput):
    """Specialized envelope output for data/object nodes."""
    
    def __init__(self, data: dict[str, Any], node_id: str, **kwargs):
        """Initialize with data dictionary.
        
        Args:
            data: Dictionary of output data
            node_id: ID of the producing node
            **kwargs: Additional metadata
        """
        envelope = EnvelopeFactory.json(data, node_id=node_id, **kwargs)
        super().__init__(envelope)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get value from the data dictionary."""
        if isinstance(self._envelope.body, dict):
            return self._envelope.body.get(key, default)
        return default


# Factory functions for easy migration
def create_text_output(content: str, node_id: str, **kwargs) -> EnvelopeOutput:
    """Create text output using envelope system."""
    return EnvelopeOutput.text(content, node_id, **kwargs)


def create_json_output(data: Any, node_id: str, **kwargs) -> EnvelopeOutput:
    """Create JSON output using envelope system."""
    return EnvelopeOutput.json(data, node_id, **kwargs)


def create_error_output(error: str | Exception, node_id: str, **kwargs) -> EnvelopeOutput:
    """Create error output using envelope system."""
    error_msg = str(error)
    error_type = type(error).__name__ if isinstance(error, Exception) else "ExecutionError"
    return EnvelopeOutput.error(error_msg, node_id, error_type=error_type, **kwargs)


def create_conversation_output(messages: list, node_id: str, **kwargs) -> ConversationEnvelopeOutput:
    """Create conversation output using envelope system."""
    return ConversationEnvelopeOutput(messages, node_id, **kwargs)


def create_condition_output(result: bool, node_id: str, 
                           true_output: Any = None, false_output: Any = None,
                           **kwargs) -> ConditionEnvelopeOutput:
    """Create condition output using envelope system."""
    return ConditionEnvelopeOutput(result, node_id, true_output, false_output, **kwargs)


def create_data_output(data: dict, node_id: str, **kwargs) -> DataEnvelopeOutput:
    """Create data output using envelope system."""
    return DataEnvelopeOutput(data, node_id, **kwargs)