"""Output builder utility for consistent envelope creation in handlers.

This utility ensures all handlers create envelopes with proper metadata,
trace IDs, and node attribution.
"""

from typing import Any
from dipeo.core.execution.envelope import get_envelope_factory


class OutputBuilder:
    """Consistent envelope creation for handlers."""
    
    def __init__(self, node_id: str, trace_id: str):
        """Initialize the output builder.
        
        Args:
            node_id: The ID of the node producing the output
            trace_id: The trace ID for the execution
        """
        self.node_id = node_id
        self.trace_id = trace_id
        self.factory = get_envelope_factory()
    
    def text(self, content: str) -> Any:
        """Create a text envelope.
        
        Args:
            content: The text content
            
        Returns:
            An Envelope with RAW_TEXT content type
        """
        return self.factory.text(
            content,
            produced_by=self.node_id,
            trace_id=self.trace_id
        )
    
    def json(self, data: Any) -> Any:
        """Create a JSON envelope.
        
        Args:
            data: The JSON-serializable data
            
        Returns:
            An Envelope with OBJECT content type
        """
        return self.factory.json(
            data,
            produced_by=self.node_id,
            trace_id=self.trace_id
        )
    
    def binary(self, data: bytes) -> Any:
        """Create a binary envelope.
        
        Args:
            data: The binary data
            
        Returns:
            An Envelope with BINARY content type
        """
        return self.factory.binary(
            data,
            produced_by=self.node_id,
            trace_id=self.trace_id
        )
    
    def error(self, msg: str, error_type: str = "ExecutionError") -> Any:
        """Create an error envelope.
        
        Args:
            msg: The error message
            error_type: The type of error
            
        Returns:
            An Envelope representing an error
        """
        return self.factory.error(
            msg,
            error_type=error_type,
            produced_by=self.node_id,
            trace_id=self.trace_id
        )