from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from dipeo.config.base_logger import get_module_logger
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.application.execution.engine.request import ExecutionRequest

logger = get_module_logger(__name__)

T = TypeVar("T", bound=ExecutableNode)
TNode = TypeVar("TNode")


class TokenHandlerMixin:
    """Mixin for handlers to support token-based execution."""

    def consume_token_inputs(self, request: ExecutionRequest) -> dict[str, Envelope] | None:
        """Consume token inputs if available. Returns None if no tokens."""
        context = request.context
        node_id = request.node.id
        return context.consume_inbound(node_id)

    def get_effective_inputs(
        self, request: ExecutionRequest, resolved_inputs: dict[str, Envelope]
    ) -> dict[str, Envelope]:
        """Get effective inputs - tokens if available, otherwise resolved inputs."""
        token_inputs = self.consume_token_inputs(request)
        if token_inputs:
            return token_inputs
        return resolved_inputs

    def emit_token_outputs(
        self, request: ExecutionRequest, output: Envelope, port: str = "default"
    ) -> None:
        context = request.context
        node_id = request.node.id

        outputs = {port: output}
        context.emit_outputs_as_tokens(node_id, outputs)


class TypedNodeHandler[T](TokenHandlerMixin, ABC):
    """Base handler for type-safe node execution with envelope communication."""

    NODE_TYPE: ClassVar[str] = ""

    def __init__(self):
        pass

    @property
    @abstractmethod
    def node_class(self) -> type[T]: ...

    @property
    def node_type(self) -> str:
        return self.NODE_TYPE

    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]: ...

    @property
    def requires_services(self) -> list[str]:
        return []

    @property
    def description(self) -> str:
        return f"Typed handler for {self.node_type} nodes"

    def validate(self, request: ExecutionRequest[T]) -> str | None:
        return None

    async def pre_execute(self, request: ExecutionRequest[T]) -> Envelope | None:
        return None

    def post_execute(self, request: ExecutionRequest[T], output: Envelope) -> Envelope:
        return output

    async def on_error(self, request: ExecutionRequest[T], error: Exception) -> Envelope | None:
        return None

    async def resolve_envelope_inputs(self, request: ExecutionRequest[T]) -> dict[str, Envelope]:
        from dipeo.domain.execution.resolution import resolve_inputs

        diagram = getattr(request.context, "diagram", None)
        if not diagram:
            return {}

        return resolve_inputs(request.node, diagram, request.context)

    async def prepare_inputs(
        self, request: ExecutionRequest[T], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        legacy_inputs = {}
        for key, envelope in inputs.items():
            try:
                legacy_inputs[key] = envelope.as_json()
            except ValueError:
                legacy_inputs[key] = envelope.as_text()
        return legacy_inputs

    @abstractmethod
    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[T]) -> Any: ...

    def serialize_output(self, result: Any, request: ExecutionRequest[T]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        # All handlers should return Envelope directly
        if isinstance(result, Envelope):
            return result

        # Fallback for dict (handlers should migrate to returning Envelope)
        elif isinstance(result, dict):
            return EnvelopeFactory.create(body=result, produced_by=node.id, trace_id=trace_id)

        elif isinstance(result, Exception):
            return EnvelopeFactory.create(
                body={"error": str(result), "type": result.__class__.__name__},
                produced_by=str(node.id),
                trace_id=trace_id,
            )

        # String fallback (handlers should migrate to returning Envelope)
        else:
            return EnvelopeFactory.create(body=str(result), produced_by=node.id, trace_id=trace_id)

    async def execute_with_envelopes(
        self, request: ExecutionRequest[T], inputs: dict[str, Envelope]
    ) -> Envelope:
        try:
            prepared_inputs = await self.prepare_inputs(request, inputs)
            result = await self.run(prepared_inputs, request)
            envelope = self.serialize_output(result, request)
            envelope = self.post_execute(request, envelope)

            # Event emission is now handled by the engine, not the handler
            return envelope

        except Exception as exc:
            logger.exception(f"Handler {self.node_type} failed: {exc}")
            custom_error = await self.on_error(request, exc)
            if custom_error:
                return custom_error
            return EnvelopeFactory.create(
                body={"error": str(exc), "type": exc.__class__.__name__},
                produced_by=str(request.node.id),
                trace_id=request.execution_id or "",
            )

    def get_required_input(self, inputs: dict[str, Envelope], key: str) -> Envelope:
        if key not in inputs:
            raise ValueError(f"Required input '{key}' not provided")
        return inputs[key]

    def get_optional_input(
        self, inputs: dict[str, Envelope], key: str, default: Any = None
    ) -> Envelope | None:
        return inputs.get(key, default)
