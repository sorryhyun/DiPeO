from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Generic, Any, Protocol
import logging
import warnings

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.core.execution.envelope import NodeOutputProtocol
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.core.execution.envelope_reader import EnvelopeReader

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ExecutableNode)
TNode = TypeVar('TNode')


class TypedNodeHandler(Generic[T], ABC):
    """Base handler for type-safe node execution with envelope communication.
    
    All handlers inherit from this class and implement execute_with_envelopes.
    Provides envelope-based input/output handling with full type safety.
    """
    
    def __init__(self):
        self.reader = EnvelopeReader()
        self._resolver = None  # Injected by engine
    
    @property
    @abstractmethod
    def node_class(self) -> type[T]:
        ...
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        ...
    
    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]:
        ...
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return f"Typed handler for {self.node_type} nodes"
    
    def validate(self, request: "ExecutionRequest[T]") -> Optional[str]:
        return None
    
    async def pre_execute(self, request: "ExecutionRequest[T]") -> Optional[NodeOutputProtocol]:
        """Pre-execution hook for checks and early returns.
        
        Called before execute_with_envelopes. If this returns a NodeOutputProtocol,
        that output is used and execute_with_envelopes is skipped.
        
        Returns:
            NodeOutputProtocol if execution should be skipped, None otherwise
        """
        return None
    
    def post_execute(
        self,
        request: "ExecutionRequest[T]",
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        return output
    
    async def on_error(
        self,
        request: "ExecutionRequest[T]",
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        return None
    
    async def resolve_envelope_inputs(
        self,
        request: "ExecutionRequest[T]"
    ) -> dict[str, Envelope]:
        """Resolve inputs as envelopes through resolver"""
        
        if not self._resolver:
            from dipeo.application.execution.resolvers import get_resolver
            self._resolver = get_resolver()
        
        # Get diagram from context
        diagram = getattr(request.context, 'diagram', None)
        if not diagram:
            # Fall back to empty inputs if no diagram available
            return {}
        
        return await self._resolver.resolve_as_envelopes(
            request.node,
            request.context,
            diagram
        )
    
    @abstractmethod
    async def execute_with_envelopes(
        self,
        request: "ExecutionRequest[T]",
        inputs: dict[str, Envelope]
    ) -> NodeOutputProtocol:
        """Handler implementation with envelopes.
        
        This is the main method to implement for envelope-aware handlers.
        """
        ...
    
    # Helper methods for handlers
    
    def get_required_input(
        self, 
        inputs: dict[str, Envelope], 
        key: str
    ) -> Envelope:
        """Get required input or raise error"""
        if key not in inputs:
            raise ValueError(f"Required input '{key}' not provided")
        return inputs[key]
    
    def get_optional_input(
        self,
        inputs: dict[str, Envelope],
        key: str,
        default: Any = None
    ) -> Envelope | None:
        """Get optional input with default"""
        return inputs.get(key, default)
    
    def create_success_output(
        self,
        *envelopes: Envelope
    ) -> NodeOutputProtocol:
        """Create successful output with envelopes"""
        
        # Return the primary envelope directly for consistent handling
        if envelopes:
            return envelopes[0]
        
        # If no envelopes provided, create an empty text envelope
        from dipeo.diagram_generated import NodeID
        return EnvelopeFactory.text("", node_id="unknown")
    
    def create_error_output(
        self,
        error: Exception,
        node_id: str | None = None,
        trace_id: str | None = None
    ) -> NodeOutputProtocol:
        """Create error output as envelope
        
        Args:
            error: Exception instance
            node_id: Node ID
            trace_id: Trace ID for tracking
        """
        from dipeo.diagram_generated import NodeID
        
        # Handle Exception case
        error_msg = str(error)
        error_type = type(error).__name__
        metadata = {}
        if node_id is None:
            node_id = "unknown"
        
        # Create error envelope using EnvelopeFactory
        error_envelope = EnvelopeFactory.error(
            error_msg,
            error_type=error_type,
            node_id=node_id,
            trace_id=trace_id or ""
        )
        
        # Add any additional metadata
        if metadata:
            error_envelope = error_envelope.with_meta(**metadata)
        
        # Return the error envelope directly for consistent handling
        return error_envelope


# For backward compatibility
TypedNodeHandlerBase = TypedNodeHandler
EnvelopeNodeHandler = TypedNodeHandler