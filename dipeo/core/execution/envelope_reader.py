import json
import io
from typing import Any, TypeVar, Type, TYPE_CHECKING
from pydantic import BaseModel, ValidationError

from .envelope import Envelope
from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np

T = TypeVar('T', bound=BaseModel)

class EnvelopeReader:
    """Safe extraction of envelope contents"""
    
    def as_text(self, envelope: Envelope) -> str:
        """Extract text content with automatic coercion"""
        if envelope.content_type == ContentType.RAW_TEXT:
            return str(envelope.body) if envelope.body is not None else ""
        elif envelope.content_type == ContentType.OBJECT:
            return json.dumps(envelope.body)
        elif envelope.content_type == ContentType.CONVERSATION_STATE:
            # Extract text from conversation
            if isinstance(envelope.body, dict):
                return envelope.body.get("last_message", "")
            return str(envelope.body)
        else:
            raise ValueError(f"Cannot convert {envelope.content_type} to text")
    
    def as_json(
        self, 
        envelope: Envelope, 
        model: Type[T] | None = None
    ) -> T | dict | list:
        """Extract and optionally validate JSON content"""
        if envelope.content_type != ContentType.OBJECT:
            # Try to parse text as JSON
            if envelope.content_type == ContentType.RAW_TEXT:
                try:
                    data = json.loads(envelope.body)
                except (json.JSONDecodeError, TypeError):
                    raise ValueError(f"Cannot parse text as JSON: {envelope.body[:100]}")
            else:
                raise ValueError(f"Cannot extract JSON from {envelope.content_type}")
        else:
            data = envelope.body
        
        # Validate with Pydantic if model provided
        if model:
            try:
                return model.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed: {e}")
        
        return data
    
    def as_conversation(self, envelope: Envelope) -> dict:
        """Extract conversation state"""
        if envelope.content_type != ContentType.CONVERSATION_STATE:
            raise ValueError(f"Expected conversation_state, got {envelope.content_type}")
        return envelope.body
    
    def as_binary(self, envelope: Envelope) -> bytes:
        """Extract binary content"""
        if envelope.content_type == ContentType.BINARY:
            if isinstance(envelope.body, bytes):
                return envelope.body
            else:
                raise ValueError(f"Binary envelope contains non-bytes data: {type(envelope.body)}")
        elif envelope.content_type == ContentType.GENERIC:
            # Backward compatibility
            return envelope.body
        elif envelope.content_type == ContentType.RAW_TEXT:
            # Try to encode text as bytes
            return envelope.body.encode('utf-8')
        else:
            raise ValueError(f"Cannot extract binary from {envelope.content_type}")
    
    def as_numpy(self, envelope: Envelope) -> "np.ndarray":
        """Extract numpy array from envelope"""
        import numpy as np
        
        if envelope.content_type != ContentType.BINARY:
            raise ValueError(f"Expected BINARY content type for numpy, got {envelope.content_type}")
        
        if envelope.serialization_format != "numpy":
            raise ValueError(f"Expected 'numpy' serialization format, got {envelope.serialization_format}")
        
        if not isinstance(envelope.body, bytes):
            raise ValueError(f"Expected bytes for numpy data, got {type(envelope.body)}")
        
        # Load numpy array from bytes
        buffer = io.BytesIO(envelope.body)
        array = np.load(buffer, allow_pickle=False)
        
        # Validate against metadata if present
        if "shape" in envelope.meta and array.shape != tuple(envelope.meta["shape"]):
            raise ValueError(f"Shape mismatch: expected {envelope.meta['shape']}, got {array.shape}")
        
        if "dtype" in envelope.meta and str(array.dtype) != envelope.meta["dtype"]:
            raise ValueError(f"Dtype mismatch: expected {envelope.meta['dtype']}, got {array.dtype}")
        
        return array
    
    def get_meta(self, envelope: Envelope, key: str, default: Any = None) -> Any:
        """Safely get metadata value"""
        return envelope.meta.get(key, default)