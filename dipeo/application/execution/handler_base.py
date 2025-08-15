from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Generic, Any, Protocol
import logging
import warnings

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ExecutableNode)
TNode = TypeVar('TNode')


class TypedNodeHandler(Generic[T], ABC):
    """Base handler for type-safe node execution with envelope communication.
    
    Uses Template Method Pattern to reduce duplication:
    - execute_with_envelopes provides the template
    - Handlers override prepare_inputs, run, and serialize_output as needed
    - Default implementations handle common cases
    """
    
    def __init__(self):
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
    
    async def pre_execute(self, request: "ExecutionRequest[T]") -> Optional[Envelope]:
        """Pre-execution hook for checks and early returns.
        
        Called before execute_with_envelopes. If this returns an Envelope,
        that output is used and execute_with_envelopes is skipped.
        
        Returns:
            Envelope if execution should be skipped, None otherwise
        """
        return None
    
    def post_execute(
        self,
        request: "ExecutionRequest[T]",
        output: Envelope
    ) -> Envelope:
        return output
    
    async def on_error(
        self,
        request: "ExecutionRequest[T]",
        error: Exception
    ) -> Optional[Envelope]:
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
    
    async def prepare_inputs(
        self,
        request: "ExecutionRequest[T]",
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs for handler execution.
        
        Default implementation converts envelopes to legacy format.
        Override this to customize input preparation.
        """
        legacy_inputs = {}
        for key, envelope in inputs.items():
            try:
                # Try to parse as JSON first
                legacy_inputs[key] = envelope.as_json()
            except ValueError:
                # Fall back to text
                legacy_inputs[key] = envelope.as_text()
        return legacy_inputs
    
    @abstractmethod
    async def run(
        self,
        inputs: dict[str, Any],
        request: "ExecutionRequest[T]"
    ) -> Any:
        """Execute the handler logic.
        
        This is the core method that handlers must implement.
        Receives prepared inputs and returns the result.
        """
        ...
    
    def serialize_output(
        self,
        result: Any,
        request: "ExecutionRequest[T]"
    ) -> Envelope:
        """Serialize handler result to envelope.
        
        Default implementation handles common cases.
        Override for custom serialization.
        """
        node = request.node
        trace_id = request.execution_id or ""
        
        # Handle different result types
        if isinstance(result, Envelope):
            # Already an envelope, return as-is
            return result
        elif isinstance(result, dict):
            # Reject deprecated {results: ...} pattern
            if set(result.keys()) == {"results"}:
                raise ValueError(
                    f"Handler {self.node_type} returned deprecated {{results: ...}} format. "
                    f"Handlers must return Envelope or list[Envelope] directly."
                )
            
            # JSON envelope for dictionaries
            return EnvelopeFactory.json(
                result,
                produced_by=node.id,
                trace_id=trace_id
            )
        elif isinstance(result, (list, tuple)):
            # Wrap lists/tuples in JSON envelope
            return EnvelopeFactory.json(
                {"default": result},
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(wrapped_list=True)
        elif isinstance(result, Exception):
            # Error envelope for exceptions
            return EnvelopeFactory.error(
                str(result),
                error_type=result.__class__.__name__,
                produced_by=str(node.id),
                trace_id=trace_id
            )
        else:
            # Text envelope for everything else
            return EnvelopeFactory.text(
                str(result),
                produced_by=node.id,
                trace_id=trace_id
            )
    
    async def execute_with_envelopes(
        self,
        request: "ExecutionRequest[T]",
        inputs: dict[str, Envelope]
    ) -> Envelope:
        """Template method for handler execution.
        
        Orchestrates the execution flow:
        1. Prepare inputs
        2. Execute handler logic
        3. Serialize output
        4. Emit completion event
        
        Handlers should override run() for their core logic,
        and optionally prepare_inputs() and serialize_output()
        for custom behavior.
        """
        try:
            # Step 1: Prepare inputs
            prepared_inputs = await self.prepare_inputs(request, inputs)
            
            # Step 2: Execute handler logic
            result = await self.run(prepared_inputs, request)
            
            # Step 3: Serialize output
            envelope = self.serialize_output(result, request)
            
            # Step 4: Emit completion event if context supports it
            if hasattr(request.context, 'emit_node_completed'):
                await request.context.emit_node_completed(
                    request.node.id,
                    envelope,
                    request.execution_id
                )
            
            return envelope
            
        except Exception as exc:
            # Handle errors consistently
            logger.exception(f"Handler {self.node_type} failed: {exc}")
            custom_error = await self.on_error(request, exc)
            if custom_error:
                return custom_error
            return EnvelopeFactory.error(
                str(exc),
                error_type=exc.__class__.__name__,
                produced_by=str(request.node.id),
                trace_id=request.execution_id or ""
            )
    
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
    
