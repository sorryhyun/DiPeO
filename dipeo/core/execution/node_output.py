"""Type-safe NodeOutput protocol hierarchy for DiPeO execution system.

This module provides a protocol-based approach to node outputs with strong typing,
clear contracts, and specialized output types for different node categories.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, Optional, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from dipeo.diagram_generated import Message, NodeID, TokenUsage, Status
    from dipeo.core.execution.envelope import Envelope

T = TypeVar('T')


@runtime_checkable
class NodeOutputProtocol(Protocol[T]):
    
    value: T
    
    metadata: str  # JSON string for intentional friction
    
    node_id: NodeID
    
    timestamp: datetime
    
    # Phase 2: Promoted typed fields
    token_usage: 'TokenUsage | None'
    execution_time: float | None
    retry_count: int
    status: 'Status | None'  # Node execution status
    
    def get_output(self, key: str, default: Any = None) -> Any:
        ...
    
    def has_error(self) -> bool:
        ...
    
    def to_dict(self) -> dict[str, Any]:
        ...
    
    def get_metadata_dict(self) -> dict[str, Any]:
        ...
    
    def set_metadata_dict(self, data: dict[str, Any]) -> None:
        ...
    
    def as_envelopes(self) -> list['Envelope']:
        """Convert to standardized envelopes"""
        ...
    
    def primary_envelope(self) -> 'Envelope':
        """Get primary output envelope"""
        ...


@dataclass
class BaseNodeOutput(Generic[T], NodeOutputProtocol[T]):
    
    value: T
    node_id: NodeID
    metadata: str = "{}"  # JSON string, requires json.loads() to access
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None
    
    # Phase 2: Promoted typed fields
    token_usage: 'TokenUsage | None' = None
    execution_time: float | None = None
    retry_count: int = 0
    status: 'Status | None' = None  # Node execution status
    
    def get_metadata_dict(self) -> dict[str, Any]:
        """Get metadata as a dictionary (creates friction for discovery)."""
        return json.loads(self.metadata) if self.metadata else {}
    
    def set_metadata_dict(self, data: dict[str, Any]) -> None:
        """Set metadata from a dictionary (creates friction for discovery)."""
        self.metadata = json.dumps(data)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        if hasattr(self.value, '__getitem__'):
            try:
                return self.value[key]
            except (KeyError, TypeError):
                pass
        
        # Parse metadata to check for key
        metadata_dict = self.get_metadata_dict()
        return metadata_dict.get(key, default)
    
    def has_error(self) -> bool:
        return self.error is not None
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "value": self.value,
            "node_id": self.node_id,
            "metadata": self.metadata,  # Keep as JSON string
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "status": self.status.value if self.status else None
        }
        
        # Include token_usage if present
        if self.token_usage:
            result["token_usage"] = {
                "input": self.token_usage.input,
                "output": self.token_usage.output,
                "cached": self.token_usage.cached,
                "total": self.token_usage.total
            }
        else:
            result["token_usage"] = None
            
        return result

    
    def primary_envelope(self) -> 'Envelope':
        """Get first/primary envelope"""
        envelopes = self.as_envelopes()
        if not envelopes:
            # Return empty envelope if none exist
            from dipeo.core.execution.envelope import EnvelopeFactory
            return EnvelopeFactory.text("")
        return envelopes[0]
    
    def with_envelopes(self, envelopes: list['Envelope']) -> 'BaseNodeOutput':
        """Set explicit envelopes"""
        self._envelopes = envelopes
        return self
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseNodeOutput:
        from dipeo.diagram_generated import TokenUsage
        
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        
        # Handle both old dict format and new string format for backwards compatibility
        metadata = data.get("metadata", "{}")
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        
        # Handle token_usage
        token_usage = None
        if "token_usage" in data and data["token_usage"]:
            token_data = data["token_usage"]
            token_usage = TokenUsage(
                input=token_data["input"],
                output=token_data["output"],
                cached=token_data.get("cached"),
                total=token_data.get("total")
            )
        
        return cls(
            value=data["value"],
            node_id=data["node_id"],
            metadata=metadata,
            timestamp=timestamp,
            error=data.get("error"),
            token_usage=token_usage,
            execution_time=data.get("execution_time"),
            retry_count=data.get("retry_count", 0)
        )


@dataclass
class TextOutput(BaseNodeOutput[str]):
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"TextOutput value must be str, got {type(self.value)}")


@dataclass
class ConversationOutput(BaseNodeOutput[list['Message']]):
    
    def __post_init__(self):
        if not isinstance(self.value, list):
            raise TypeError(f"ConversationOutput value must be list, got {type(self.value)}")
    
    def get_last_message(self) -> Optional["Message"]:
        return self.value[-1] if self.value else None
    
    def get_messages_by_role(self, role: str) -> list['Message']:
        return [msg for msg in self.value if hasattr(msg, 'role') and msg.role == role]


@dataclass
class ConditionOutput(BaseNodeOutput[bool]):
    
    true_output: Any = None  # Data for true branch
    false_output: Any = None  # Data for false branch
    
    def __post_init__(self):
        if not isinstance(self.value, bool):
            raise TypeError(f"ConditionOutput value must be bool, got {type(self.value)}")
        
        # Use set_metadata_dict to maintain JSON string format
        self.set_metadata_dict({
            "condtrue": self.true_output,
            "condfalse": self.false_output,
            "active_branch": "condtrue" if self.value else "condfalse"
        })
    
    def get_branch_output(self) -> tuple[str, Any]:
        if self.value:
            return ("condtrue", self.true_output)
        else:
            return ("condfalse", self.false_output)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        if key in ["condtrue", "condfalse", "active_branch"]:
            metadata_dict = self.get_metadata_dict()
            return metadata_dict.get(key, default)
        return super().get_output(key, default)


@dataclass
class DataOutput(BaseNodeOutput[dict[str, Any]]):
    
    def __post_init__(self):
        if not isinstance(self.value, dict):
            raise TypeError(f"DataOutput value must be dict, got {type(self.value)}")
    
    def get_output(self, key: str, default: Any = None) -> Any:
        return self.value.get(key, default)


@dataclass
class ErrorOutput(BaseNodeOutput[str]):
    
    error_type: str = "ExecutionError"
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"ErrorOutput value must be str, got {type(self.value)}")
        
        self.error = self.value
        # Use set_metadata_dict to maintain JSON string format
        self.set_metadata_dict({
            "error_type": self.error_type,
            "is_error": True
        })
    
    def has_error(self) -> bool:
        return True


# Phase 2: Specialized output classes for high-usage nodes

@dataclass
class PersonJobOutput(ConversationOutput):
    """Specialized output for PersonJob nodes with required token usage."""
    
    person_id: str | None = None
    conversation_id: str | None = None
    model: str | None = None  # LLM model used for this execution
    
    def __post_init__(self):
        super().__post_init__()
        # PersonJob nodes should always have token usage
        if self.token_usage is None:
            # Initialize with zeros if not provided
            from dipeo.diagram_generated import TokenUsage
            self.token_usage = TokenUsage(input=0, output=0, total=0)


@dataclass
class CodeJobOutput(TextOutput):
    """Specialized output for CodeJob nodes with execution details."""
    
    language: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    result_type: str | None = None  # Type of result (dict, string, etc.)
    
    def __post_init__(self):
        super().__post_init__()
        # Code execution should track execution time
        if self.execution_time is None:
            self.execution_time = 0.0


@dataclass
class APIJobOutput(DataOutput):
    """Specialized output for APIJob nodes with HTTP details."""
    
    status_code: int | None = None
    headers: dict[str, str] | None = None
    response_time: float | None = None
    url: str | None = None  # The URL that was called
    method: str | None = None  # HTTP method used
    
    def __post_init__(self):
        super().__post_init__()
        # Use response_time to populate execution_time
        if self.response_time is not None and self.execution_time is None:
            self.execution_time = self.response_time


@dataclass
class TemplateJobOutput(TextOutput):
    """Specialized output for TemplateJob nodes with rendering details."""
    
    engine: str | None = None  # Template engine used (jinja2, internal, etc.)
    template_path: str | None = None  # Path to template file if used
    output_path: str | None = None  # Path where output was written if applicable
    
    def __post_init__(self):
        super().__post_init__()
        # Template rendering should track execution time
        if self.execution_time is None:
            self.execution_time = 0.0


def serialize_protocol(output: NodeOutputProtocol) -> dict[str, Any]:
    """Serialize protocol output for storage with type preservation.
    
    Supports both NodeOutput and Envelope instances for seamless migration.
    """
    # Import here to avoid circular dependency
    from dipeo.core.execution.envelope import Envelope
    from dipeo.core.execution.envelope_output import EnvelopeOutput
    
    # Handle Envelope instances directly
    if isinstance(output, Envelope):
        return {
            "_protocol_type": "Envelope",
            "_envelope_format": True,
            "id": output.id,
            "trace_id": output.trace_id,
            "produced_by": output.produced_by,
            "content_type": output.content_type,
            "schema_id": output.schema_id,
            "serialization_format": output.serialization_format,
            "body": output.body,
            "meta": output.meta
        }
    
    # Handle EnvelopeOutput adapter
    if isinstance(output, EnvelopeOutput):
        envelope = output.primary_envelope()
        return serialize_protocol(envelope)
    
    # Legacy NodeOutput serialization
    base_dict = {
        "_protocol_type": output.__class__.__name__,
        "value": output.value,
        "metadata": output.metadata,  # Already a JSON string
        "node_id": str(output.node_id),
        "execution_time": output.execution_time,
        "retry_count": output.retry_count
    }
    
    # Include token_usage if present
    if output.token_usage:
        base_dict["token_usage"] = {
            "input": output.token_usage.input,
            "output": output.token_usage.output,
            "cached": output.token_usage.cached,
            "total": output.token_usage.total
        }
    else:
        base_dict["token_usage"] = None
    
    if isinstance(output, ConditionOutput):
        base_dict["true_output"] = output.true_output
        base_dict["false_output"] = output.false_output
    elif isinstance(output, ErrorOutput):
        base_dict["error"] = output.error
        base_dict["error_type"] = output.error_type
    elif isinstance(output, PersonJobOutput):
        base_dict["person_id"] = output.person_id
        base_dict["conversation_id"] = output.conversation_id
        base_dict["model"] = output.model
    elif isinstance(output, CodeJobOutput):
        base_dict["language"] = output.language
        base_dict["stdout"] = output.stdout
        base_dict["stderr"] = output.stderr
        base_dict["result_type"] = output.result_type
    elif isinstance(output, APIJobOutput):
        base_dict["status_code"] = output.status_code
        base_dict["headers"] = output.headers
        base_dict["response_time"] = output.response_time
        base_dict["url"] = output.url
        base_dict["method"] = output.method
    elif isinstance(output, TemplateJobOutput):
        base_dict["engine"] = output.engine
        base_dict["template_path"] = output.template_path
        base_dict["output_path"] = output.output_path
    elif isinstance(output, DataOutput):
        pass
    elif isinstance(output, TextOutput):
        pass
    
    return base_dict


def deserialize_protocol(data: dict[str, Any]) -> NodeOutputProtocol:
    """Reconstruct protocol output from stored data with type information.
    
    Supports both NodeOutput and Envelope formats for seamless migration.
    """
    from dipeo.diagram_generated import TokenUsage, NodeID, Status
    
    # Check if this is an Envelope format
    if data.get("_envelope_format") or data.get("_protocol_type") == "Envelope":
        from dipeo.core.execution.envelope import Envelope
        from dipeo.diagram_generated.enums import ContentType
        
        # Convert content_type string to enum if needed
        content_type = data.get("content_type", ContentType.RAW_TEXT)
        if isinstance(content_type, str):
            content_type = ContentType(content_type)
        
        return Envelope(
            id=data.get("id", ""),
            trace_id=data.get("trace_id", ""),
            produced_by=data.get("produced_by", "system"),
            content_type=content_type,
            schema_id=data.get("schema_id"),
            serialization_format=data.get("serialization_format"),
            body=data.get("body"),
            meta=data.get("meta", {})
        )
    
    # Legacy NodeOutput deserialization
    protocol_type = data.get("_protocol_type", "BaseNodeOutput")
    node_id = NodeID(data["node_id"])
    value = data["value"]
    
    # Handle both old dict format and new string format for backwards compatibility
    metadata = data.get("metadata", "{}")
    if isinstance(metadata, dict):
        metadata = json.dumps(metadata)
    
    # Handle token_usage
    token_usage = None
    if "token_usage" in data and data["token_usage"]:
        token_data = data["token_usage"]
        token_usage = TokenUsage(
            input=token_data["input"],
            output=token_data["output"],
            cached=token_data.get("cached"),
            total=token_data.get("total")
        )
    
    # Common fields for all outputs
    common_kwargs = {
        "value": value,
        "node_id": node_id,
        "metadata": metadata,
        "token_usage": token_usage,
        "execution_time": data.get("execution_time"),
        "retry_count": data.get("retry_count", 0)
    }
    
    if protocol_type == "ConditionOutput":
        common_kwargs["value"] = bool(value)
        return ConditionOutput(
            **common_kwargs,
            true_output=data.get("true_output"),
            false_output=data.get("false_output")
        )
    elif protocol_type == "ErrorOutput":
        common_kwargs["value"] = str(value)
        return ErrorOutput(
            **common_kwargs,
            error=data.get("error", str(value)),
            error_type=data.get("error_type", "UnknownError")
        )
    elif protocol_type == "PersonJobOutput":
        return PersonJobOutput(
            **common_kwargs,
            person_id=data.get("person_id"),
            conversation_id=data.get("conversation_id"),
            model=data.get("model")
        )
    elif protocol_type == "CodeJobOutput":
        common_kwargs["value"] = str(value)
        return CodeJobOutput(
            **common_kwargs,
            language=data.get("language"),
            stdout=data.get("stdout"),
            stderr=data.get("stderr"),
            result_type=data.get("result_type")
        )
    elif protocol_type == "APIJobOutput":
        common_kwargs["value"] = dict(value) if not isinstance(value, dict) else value
        return APIJobOutput(
            **common_kwargs,
            status_code=data.get("status_code"),
            headers=data.get("headers"),
            response_time=data.get("response_time"),
            url=data.get("url"),
            method=data.get("method")
        )
    elif protocol_type == "TemplateJobOutput":
        common_kwargs["value"] = str(value)
        return TemplateJobOutput(
            **common_kwargs,
            engine=data.get("engine"),
            template_path=data.get("template_path"),
            output_path=data.get("output_path")
        )
    elif protocol_type == "TextOutput":
        common_kwargs["value"] = str(value)
        return TextOutput(**common_kwargs)
    elif protocol_type == "DataOutput":
        common_kwargs["value"] = dict(value) if not isinstance(value, dict) else value
        return DataOutput(**common_kwargs)
    else:
        return BaseNodeOutput(**common_kwargs)