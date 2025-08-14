from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Generic, Any, Protocol
import logging
import warnings

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.core.execution.node_output import NodeOutputProtocol, BaseNodeOutput, ErrorOutput
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
        from dipeo.diagram_generated import NodeID
        
        # Get the primary envelope's content as the value
        value = ""
        if envelopes:
            primary = envelopes[0]
            value = primary.body if primary.body is not None else ""
        
        # Create output with proper node_id
        node_id = NodeID(envelopes[0].produced_by) if envelopes else NodeID("unknown")
        output = BaseNodeOutput(value=value, node_id=node_id)
        output._envelopes = list(envelopes)
        return output
    
    def create_error_output(
        self,
        error: Exception,
        node_id: str,
        trace_id: str
    ) -> NodeOutputProtocol:
        """Create error output as envelope"""
        from dipeo.diagram_generated import NodeID
        
        error_envelope = EnvelopeFactory.json(
            {
                "error": str(error),
                "type": type(error).__name__,
                "node": node_id
            },
            produced_by=node_id,
            trace_id=trace_id
        )
        
        # Create ErrorOutput with proper node_id
        node_id_obj = NodeID(node_id)
        output = ErrorOutput(
            value=str(error),
            node_id=node_id_obj,
            error_type=type(error).__name__
        )
        output._envelopes = [error_envelope]
        return output


# For backward compatibility
TypedNodeHandlerBase = TypedNodeHandler
EnvelopeNodeHandler = TypedNodeHandler