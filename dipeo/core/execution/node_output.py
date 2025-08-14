"""Type-safe NodeOutput protocol for DiPeO execution system.

This module provides a protocol-based approach to node outputs with strong typing
and clear contracts. All concrete implementations now use the Envelope system.
"""

from __future__ import annotations

import json
from abc import abstractmethod
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
    
    # For any other NodeOutputProtocol implementation, use the protocol methods
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
    
    return base_dict


def deserialize_protocol(data: dict[str, Any]) -> NodeOutputProtocol:
    """Reconstruct protocol output from stored data with type information.
    
    Now only supports Envelope format as all NodeOutput classes have been removed.
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
    
    # Legacy format - convert to Envelope
    from dipeo.core.execution.envelope import EnvelopeFactory
    from dipeo.diagram_generated.enums import ContentType
    
    node_id = data.get("node_id", "unknown")
    value = data.get("value")
    metadata = data.get("metadata", "{}")
    
    # Parse metadata if it's a JSON string
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    # Determine content type based on protocol type
    protocol_type = data.get("_protocol_type", "")
    if "Condition" in protocol_type:
        content_type = ContentType.CONDITION_RESULT
    elif "Conversation" in protocol_type:
        content_type = ContentType.CONVERSATION_STATE
    elif "Data" in protocol_type or isinstance(value, dict):
        content_type = ContentType.OBJECT
    else:
        content_type = ContentType.RAW_TEXT
    
    # Create metadata for envelope
    meta = {}
    if data.get("token_usage"):
        meta["token_usage"] = data["token_usage"]
    if data.get("execution_time") is not None:
        meta["execution_time"] = data["execution_time"]
    if data.get("retry_count"):
        meta["retry_count"] = data["retry_count"]
    
    # Add condition-specific metadata
    if "Condition" in protocol_type:
        meta["condtrue"] = data.get("true_output")
        meta["condfalse"] = data.get("false_output")
        meta["active_branch"] = "condtrue" if value else "condfalse"
    
    # Add any existing metadata
    if metadata:
        meta.update(metadata)
    
    return EnvelopeFactory.create(
        content_type=content_type,
        body=value,
        node_id=str(node_id),
        meta=meta
    )