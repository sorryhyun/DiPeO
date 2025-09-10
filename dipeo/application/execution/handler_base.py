from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=ExecutableNode)
TNode = TypeVar("TNode")


class TokenHandlerMixin:
    """Mixin for handlers to support token-based execution."""

    def consume_token_inputs(
        self, request: ExecutionRequest, fallback_inputs: dict[str, Envelope]
    ) -> dict[str, Envelope]:
        context = request.context
        node_id = request.node.id

        token_inputs = context.consume_inbound(node_id)
        return token_inputs if token_inputs else fallback_inputs

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

        if isinstance(result, Envelope):
            return result
        elif isinstance(result, dict):
            if set(result.keys()) == {"results"}:
                raise ValueError(
                    f"Handler {self.node_type} returned deprecated {{results: ...}} format. "
                    f"Handlers must return Envelope or list[Envelope] directly."
                )
            return EnvelopeFactory.create(body=result, produced_by=node.id, trace_id=trace_id)
        elif isinstance(result, list | tuple):
            return EnvelopeFactory.create(
                body={"default": result}, produced_by=node.id, trace_id=trace_id
            ).with_meta(wrapped_list=True)
        elif isinstance(result, Exception):
            return EnvelopeFactory.create(
                body={"error": str(result), "type": result.__class__.__name__},
                produced_by=str(node.id),
                trace_id=trace_id,
            )
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

            if hasattr(request.context, "events"):
                exec_count = request.context.state.get_node_execution_count(request.node.id)
                await request.context.events.emit_node_completed(request.node, envelope, exec_count)

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
