"""Main PersonJobNodeHandler class - coordinates single and batch execution."""

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import (
    Optional,
    Required,
    requires_services,
)
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import (
    DIAGRAM,
    EXECUTION_ORCHESTRATOR,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    PROMPT_BUILDER,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

from .batch_executor import BatchExecutor
from .conversation_handler import ConversationHandler
from .output_builder import OutputBuilder
from .single_executor import SingleExecutor
from .text_format_handler import TextFormatHandler

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    llm_service=(LLM_SERVICE, Required),
    diagram=(DIAGRAM, Required),
    execution_orchestrator=(EXECUTION_ORCHESTRATOR, Required),
    prompt_builder=(PROMPT_BUILDER, Required),
    filesystem_adapter=(FILESYSTEM_ADAPTER, Optional),
)
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    """Coordinates AI person job execution through specialized executors, supporting both single and batch modes."""

    NODE_TYPE = NodeType.PERSON_JOB.value

    def __init__(self):
        super().__init__()

        self._text_format_handler = TextFormatHandler()
        self._conversation_handler = ConversationHandler()
        self._output_builder = OutputBuilder(self._text_format_handler, self._conversation_handler)

        self._single_executor = None
        self._batch_executor = None

    @property
    def node_class(self) -> type[PersonJobNode]:
        return PersonJobNode

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNode

    @property
    def node_type(self) -> str:
        return NodeType.PERSON_JOB.value

    @property
    def requires_services(self) -> list[str]:
        return self.get_required_services() + self.get_optional_services()

    @property
    def description(self) -> str:
        return (
            "Execute person job with conversation memory, "
            "supporting both single and batch execution"
        )

    def _ensure_executors(self):
        if self._single_executor is None:
            self._single_executor = SingleExecutor(
                llm_service=self._llm_service,
                diagram=self._diagram,
                execution_orchestrator=self._execution_orchestrator,
                prompt_builder=self._prompt_builder,
                output_builder=self._output_builder,
                conversation_handler=self._conversation_handler,
            )

        if self._batch_executor is None:
            self._batch_executor = BatchExecutor(
                execute_single_callback=self._execute_single_wrapper
            )

    async def _execute_single_wrapper(
        self, request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        self._ensure_executors()
        return await self._single_executor.execute(request)

    def validate(self, request: ExecutionRequest[PersonJobNode]) -> str | None:
        node = request.node

        if not node.person:
            return "No person specified"

        if getattr(node, "batch", False):
            batch_input_key = getattr(node, "batch_input_key", "items")
            if not batch_input_key:
                return "Batch mode enabled but batch_input_key not specified"

        return None

    async def pre_execute(self, request: ExecutionRequest[PersonJobNode]) -> Envelope | None:
        request.set_handler_state("debug", False)
        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[PersonJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        node = request.node

        envelope_inputs = self.get_effective_inputs(request, inputs)
        inputs = envelope_inputs

        prompt_envelope = self.get_optional_input(inputs, "prompt")
        prompt = None
        if prompt_envelope:
            prompt = prompt_envelope.as_text()
        else:
            has_prompt_file = getattr(node, "prompt_file", None) or getattr(
                node, "first_prompt_file", None
            )
            has_resolved_prompt = getattr(node, "resolved_prompt", None) or getattr(
                node, "resolved_first_prompt", None
            )
            prompt = getattr(node, "default_prompt", None)

            if not prompt and not has_prompt_file and not has_resolved_prompt:
                raise ValueError(
                    f"No prompt provided and no default_prompt, prompt_file, "
                    f"or resolved_prompt configured for node {node.id}"
                )

        context_data = None
        if context_envelope := self.get_optional_input(inputs, "context"):
            try:
                context_data = context_envelope.as_json()
            except ValueError:
                context_data = context_envelope.as_text()

        conversation_state = None
        if conv_envelope := self.get_optional_input(inputs, "_conversation"):
            conversation_state = conv_envelope.as_conversation()

        processed_inputs = {}
        for key, envelope in inputs.items():
            if envelope.content_type == "raw_text":
                processed_inputs[key] = envelope.as_text()
            elif envelope.content_type == "object":
                processed_inputs[key] = envelope.as_json()
            elif envelope.content_type == "conversation_state":
                processed_inputs[key] = envelope.as_conversation()
            else:
                processed_inputs[key] = envelope.body

        if prompt is not None:
            processed_inputs["prompt"] = prompt
        if context_data is not None:
            processed_inputs["context"] = context_data
        if conversation_state:
            processed_inputs["_conversation"] = conversation_state

        return processed_inputs

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[PersonJobNode]) -> Any:
        node = request.node
        request.inputs = inputs

        self._ensure_executors()

        if self._filesystem_adapter:
            from dipeo.application.execution.use_cases import PromptLoadingUseCase

            prompt_loading_use_case = PromptLoadingUseCase(self._filesystem_adapter)
            request.set_handler_state("prompt_loading_use_case", prompt_loading_use_case)

        if getattr(node, "batch", False):
            logger.info(f"Executing PersonJobNode {node.id} in batch mode")
            return await self._batch_executor.execute_batch(request)
        else:
            return await self._single_executor.execute(request)

    def serialize_output(self, result: Any, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        if getattr(node, "batch", False):
            if isinstance(result, dict) and "value" in result:
                output_envelope = EnvelopeFactory.create(
                    body=result["value"], produced_by=node.id, trace_id=trace_id
                ).with_meta(batch_mode=True, person_id=node.person)
                return output_envelope
            else:
                logger.warning(f"Unexpected batch result format: {type(result)}")
                output_envelope = EnvelopeFactory.create(
                    body=str(result), produced_by=node.id, trace_id=trace_id
                )
                return output_envelope
        else:
            if isinstance(result, dict) and "body" in result and "metadata" in result:
                body = result["body"]
                metadata = result["metadata"]
                representations = metadata.pop("representations", {})

                output_envelope = EnvelopeFactory.create(
                    body=body, produced_by=node.id, trace_id=trace_id, meta=metadata
                )

                if representations:
                    output_envelope = output_envelope.with_meta(representations=representations)

                return output_envelope
            else:
                logger.warning(f"Unexpected result type from _execute_single: {type(result)}")
                output_envelope = EnvelopeFactory.create(
                    body=str(result), produced_by=node.id, trace_id=trace_id
                )
                return output_envelope

    async def on_error(
        self, request: ExecutionRequest[PersonJobNode], error: Exception
    ) -> Envelope | None:
        trace_id = request.execution_id or ""

        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return EnvelopeFactory.create(
                body={"error": f"ValidationError: {error}", "type": "ValueError"},
                produced_by=request.node.id,
                trace_id=trace_id,
            )

        logger.error(f"Error executing person job: {error}")
        return EnvelopeFactory.create(
            body={"error": str(error), "type": error.__class__.__name__},
            produced_by=request.node.id,
            trace_id=trace_id,
        )

    def post_execute(self, request: ExecutionRequest[PersonJobNode], output: Envelope) -> Envelope:
        debug = request.get_handler_state("debug", False)
        if debug:
            is_batch = getattr(request.node, "batch", False)
            if is_batch:
                batch_info = output.value if hasattr(output, "value") else {}
                total = batch_info.get("total_items", 0)
                successful = batch_info.get("successful", 0)
                logger.debug(f"Batch person job completed: {successful}/{total} successful")
            else:
                logger.debug(f"Person job completed for {request.node.person}")

        self.emit_token_outputs(request, output)

        return output
