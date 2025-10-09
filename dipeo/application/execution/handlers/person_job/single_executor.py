"""Single execution logic for PersonJobNode - handles template processing and LLM calls."""

from typing import Any

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.utils import get_node_execution_count
from dipeo.config.base_logger import get_module_logger
from dipeo.config.llm import PERSON_JOB_MAX_TOKENS, PERSON_JOB_TEMPERATURE
from dipeo.diagram_generated.domain_models import PersonID
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.execution.envelope import EnvelopeFactory
from dipeo.infrastructure.timing.context import atime_phase, time_phase

from .conversation_handler import ConversationHandler
from .output_builder import OutputBuilder

logger = get_module_logger(__name__)


class SingleExecutor:
    """Handles single-person execution for PersonJob nodes.

    This class encapsulates all logic for executing a person job for a single person,
    including template processing, LLM calls, and conversation handling.
    """

    def __init__(
        self,
        llm_service: Any,
        diagram: Any,
        execution_orchestrator: Any,
        prompt_builder: Any,
        output_builder: OutputBuilder,
        conversation_handler: ConversationHandler,
    ):
        """Initialize SingleExecutor with required dependencies.

        Args:
            llm_service: LLM service for AI calls
            diagram: Diagram containing node definitions
            execution_orchestrator: Orchestrator for execution context
            prompt_builder: Builder for prompt templates
            output_builder: Builder for output formatting
            conversation_handler: Handler for conversation operations
        """
        self._llm_service = llm_service
        self._diagram = diagram
        self._execution_orchestrator = execution_orchestrator
        self._prompt_builder = prompt_builder
        self._output_builder = output_builder
        self._conversation_handler = conversation_handler

    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> dict[str, Any]:
        """Execute the person job for a single person.

        Args:
            request: Execution request containing node, context, and inputs

        Returns:
            Dictionary with body and metadata
        """
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        inputs = request.inputs

        person_id = node.person
        execution_count = get_node_execution_count(context, node.id)

        if not self._execution_orchestrator:
            raise ValueError(f"ExecutionOrchestrator not available for person {person_id}")

        person = self._execution_orchestrator.get_or_create_person(
            PersonID(person_id), diagram=self._diagram
        )

        with time_phase(trace_id, node.id, "input_extraction"):
            extracted_inputs = self._extract_inputs(inputs)

        has_conversation_input = self._conversation_handler.has_conversation_input(extracted_inputs)
        if has_conversation_input:
            messages_to_add = self._conversation_handler.load_conversation_from_inputs(
                extracted_inputs, str(person.id)
            )
            if messages_to_add and hasattr(self._execution_orchestrator, "add_message"):
                for msg in messages_to_add:
                    self._execution_orchestrator.add_message(
                        msg, execution_id=trace_id, node_id=str(node.id)
                    )

        all_messages = (
            self._execution_orchestrator.get_conversation().messages
            if hasattr(self._execution_orchestrator, "get_conversation")
            else []
        )

        prompt_content = node.default_prompt
        first_only_content = node.first_only_prompt

        # Check for pre-resolved prompts
        if hasattr(node, "resolved_first_prompt") and node.resolved_first_prompt:
            first_only_content = node.resolved_first_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved first prompt")

        if hasattr(node, "resolved_prompt") and node.resolved_prompt:
            prompt_content = node.resolved_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved default prompt")

        memorize_to = getattr(node, "memorize_to", None)
        at_most = getattr(node, "at_most", None)
        ignore_person = getattr(node, "ignore_person", None)

        input_values = self._prompt_builder.prepare_template_values(extracted_inputs)
        logger.debug(f"[PersonJob] input_values keys after prepare: {list(input_values.keys())}")

        template_values = context.build_template_context(inputs=input_values, globals_win=True)

        with time_phase(trace_id, node.id, "prompt_building"):
            built_prompt = self._prompt_builder.build(
                prompt=prompt_content,
                template_values=template_values,
                first_only_prompt=first_only_content,
                execution_count=execution_count,
            )

        if "{{" in (built_prompt or ""):
            logger.warning(
                f"[PersonJob {node.label or node.id}] Template variables may not be "
                f"substituted! Found '{{{{' in built prompt"
            )

        if not built_prompt:
            logger.warning(f"Skipping execution for person {person_id} - no prompt available")
            return EnvelopeFactory.create(body="", produced_by=str(node.id), trace_id=trace_id)

        complete_kwargs = self._prepare_llm_kwargs(node, built_prompt, trace_id)

        task_preview = self._build_task_preview(
            memorize_to,
            at_most,
            prompt_content,
            first_only_content,
            template_values,
            execution_count,
        )

        async with atime_phase(trace_id, node.id, "complete_with_memory"):
            (
                result,
                incoming_msg,
                response_msg,
                selected_messages,
            ) = await person.complete_with_memory(
                all_messages=all_messages,
                memorize_to=memorize_to,
                ignore_person=ignore_person,
                at_most=at_most,
                prompt_preview=task_preview,
                execution_id=trace_id,
                node_id=str(node.id),
                **complete_kwargs,
            )

        if hasattr(self._execution_orchestrator, "add_message"):
            self._execution_orchestrator.add_message(
                incoming_msg, execution_id=trace_id, node_id=str(node.id)
            )
            self._execution_orchestrator.add_message(
                response_msg, execution_id=trace_id, node_id=str(node.id)
            )

        with time_phase(trace_id, node.id, "output_building"):
            output = self._output_builder.build_single_output(
                result=result,
                person=person,
                node=node,
                diagram=self._diagram,
                model=person.llm_config.model,
                trace_id=trace_id,
                selected_messages=selected_messages,
                execution_orchestrator=self._execution_orchestrator,
            )

        return output

    def _extract_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Extract values from Envelope objects for template processing.

        Args:
            inputs: Input dictionary potentially containing Envelope objects

        Returns:
            Dictionary with extracted values
        """
        extracted_inputs = {}
        for key, value in inputs.items():
            if hasattr(value, "body"):
                body = value.body
                # Filter out internal metadata from conversation outputs
                if isinstance(body, dict) and "llm_usage" in body:
                    body = {k: v for k, v in body.items() if k != "llm_usage"}
                extracted_inputs[key] = body
            else:
                extracted_inputs[key] = value
        return extracted_inputs

    def _prepare_llm_kwargs(
        self, node: PersonJobNode, built_prompt: str, trace_id: str
    ) -> dict[str, Any]:
        """Prepare LLM call arguments.

        Args:
            node: PersonJobNode containing configuration
            built_prompt: Built prompt text
            trace_id: Execution trace ID

        Returns:
            Dictionary of LLM kwargs
        """
        complete_kwargs = {
            "prompt": built_prompt,
            "llm_service": self._llm_service,
            "from_person_id": "system",
            "temperature": PERSON_JOB_TEMPERATURE,
            "max_tokens": PERSON_JOB_MAX_TOKENS,
        }

        # Pass trace_id for workspace directory creation in claude-code
        complete_kwargs["trace_id"] = trace_id

        if hasattr(node, "tools") and node.tools and node.tools != "none":
            tools_config = []
            if node.tools == "image":
                from dipeo.diagram_generated.domain_models import ToolConfig, ToolType

                tools_config.append(ToolConfig(type=ToolType.IMAGE_GENERATION, enabled=True))
            elif node.tools == "websearch":
                from dipeo.diagram_generated.domain_models import ToolConfig, ToolType

                tools_config.append(ToolConfig(type=ToolType.WEB_SEARCH, enabled=True))
            if tools_config:
                complete_kwargs["tools"] = tools_config

        from .text_format_handler import TextFormatHandler

        text_format_handler = TextFormatHandler()
        pydantic_model = text_format_handler.get_pydantic_model(node)
        if pydantic_model:
            complete_kwargs["text_format"] = pydantic_model

        return complete_kwargs

    def _build_task_preview(
        self,
        memorize_to: str | None,
        at_most: int | None,
        prompt_content: str | None,
        first_only_content: str | None,
        template_values: dict[str, Any],
        execution_count: int,
    ) -> str | None:
        """Build task preview for memory selection.

        Args:
            memorize_to: Memory selection strategy
            at_most: Maximum messages to include
            prompt_content: Default prompt content
            first_only_content: First-only prompt content
            template_values: Template values for substitution
            execution_count: Current execution count

        Returns:
            Task preview string or None
        """
        if not (memorize_to or at_most):
            return None

        task_preview_raw = prompt_content or first_only_content or ""
        task_preview = self._prompt_builder.build(
            prompt=task_preview_raw,
            template_values=template_values,
            first_only_prompt=None,
            execution_count=execution_count,
        )
        return task_preview
