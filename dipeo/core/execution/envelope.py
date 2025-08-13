from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any
from uuid import uuid4
import time

from dipeo.diagram_generated.enums import ContentType

@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication"""
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default="")
    
    # Source
    produced_by: str = field(default="system")
    
    # Content
    content_type: ContentType = field(default="raw_text")
    schema_id: str | None = field(default=None)
    body: Any = field(default=None)
    
    # Metadata
    meta: dict[str, Any] = field(default_factory=dict)
    
    def with_meta(self, **kwargs) -> Envelope:
        """Create new envelope with updated metadata"""
        new_meta = {**self.meta, **kwargs}
        return replace(self, meta=new_meta)
    
    def with_iteration(self, iteration: int) -> Envelope:
        """Tag with iteration number"""
        return self.with_meta(iteration=iteration)
    
    def with_branch(self, branch_id: str) -> Envelope:
        """Tag with branch identifier"""
        return self.with_meta(branch_id=branch_id)

class EnvelopeFactory:
    """Factory for creating envelopes"""
    
    @staticmethod
    def text(content: str, **kwargs) -> Envelope:
        return Envelope(
            content_type=ContentType.RAW_TEXT,
            body=content,
            meta={"timestamp": time.time()},
            **kwargs
        )
    
    @staticmethod
    def json(data: Any, schema_id: str | None = None, **kwargs) -> Envelope:
        return Envelope(
            content_type=ContentType.OBJECT,
            schema_id=schema_id,
            body=data,
            meta={"timestamp": time.time()},
            **kwargs
        )
    
    @staticmethod
    def conversation(state: dict, **kwargs) -> Envelope:
        return Envelope(
            content_type=ContentType.CONVERSATION_STATE,
            body=state,
            meta={"timestamp": time.time()},
            **kwargs
        )