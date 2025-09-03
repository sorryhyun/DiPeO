from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Generic, Any, Protocol, ClassVar
import logging
import warnings

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ExecutableNode)
TNode = TypeVar('TNode')


class TokenHandlerMixin:
    """Mixin for handlers to support token-based execution.
    
    Phase 5: Provides common token consumption and emission logic for gradual migration.
    Handlers can override these methods for custom behavior.
    """
    
    def consume_token_inputs(
        self,
        request: "ExecutionRequest",
        fallback_inputs: dict[str, Envelope]
    ) -> dict[str, Envelope]:
        """Consume tokens from incoming edges or fall back to regular inputs.
        
        Args:
            request: The execution request
            fallback_inputs: Regular inputs to use if no tokens available
            
        Returns:
            Dict of port name to envelope
        """
        context = request.context
        node_id = request.node.id
        
        # Try to consume tokens from incoming edges
        token_inputs = context.consume_inbound(node_id)
        
        # Use token inputs if available, otherwise fall back
        if token_inputs:
            logger.debug(f"[TOKEN] Handler {node_id} consumed {len(token_inputs)} token inputs")
            return token_inputs
        else:
            logger.debug(f"[TOKEN] Handler {node_id} using fallback inputs (no tokens available)")
            return fallback_inputs
    
    def emit_token_outputs(
        self,
        request: "ExecutionRequest",
        output: Envelope,
        port: str = "default"
    ) -> None:
        """Emit output envelope as tokens on outgoing edges.
        
        Args:
            request: The execution request
            output: The output envelope to emit
            port: The output port name (default: "default")
        """
        context = request.context
        node_id = request.node.id
        
        # Wrap output in dict for emit_outputs_as_tokens
        outputs = {port: output}
        
        # Emit as tokens on all outgoing edges
        context.emit_outputs_as_tokens(node_id, outputs)
        logger.debug(f"[TOKEN] Handler {node_id} emitted output as tokens on port '{port}'")


class TypedNodeHandler(Generic[T], TokenHandlerMixin, ABC):
    """Base handler for type-safe node execution with envelope communication.
    
    Uses Template Method Pattern to reduce duplication:
    - execute_with_envelopes provides the template
    - Handlers override prepare_inputs, run, and serialize_output as needed
    - Default implementations handle common cases
    
    Includes TokenHandlerMixin for token-based execution support (Phase 5).
    """
    
    # Class variable to avoid instantiation at registration
    NODE_TYPE: ClassVar[str] = ""
    
    def __init__(self):
        # Resolver no longer needed - using domain resolution directly
        pass
    
    @property
    @abstractmethod
    def node_class(self) -> type[T]:
        ...
    
    @property
    def node_type(self) -> str:
        """Get node type from class variable."""
        return self.NODE_TYPE
    
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
        """Resolve inputs as envelopes using domain resolution directly"""
        import logging
        from dipeo.domain.execution.resolution import resolve_inputs
        
        logger = logging.getLogger(__name__)
        
        # Get diagram from context
        diagram = getattr(request.context, 'diagram', None)
        if not diagram:
            # Fall back to empty inputs if no diagram available
            return {}
        
        # Use domain resolution directly (it's synchronous)
        result = resolve_inputs(request.node, diagram, request.context)
        return result
    
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
                exec_count = request.context.get_node_execution_count(request.node.id)
                await request.context.emit_node_completed(
                    request.node,
                    envelope,
                    exec_count
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
    
