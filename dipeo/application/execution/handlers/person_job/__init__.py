"""Handler for PersonJobNode - executes AI person jobs with conversation memory.

This refactored version merges the executor logic directly into the handler,
reducing layers of abstraction from 8 to 4-5 as per the simplification plan.
"""

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import (
    Optional,
    Required,
    requires_services,
)
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.use_cases import PromptLoadingUseCase
from dipeo.application.registry.keys import (
    DIAGRAM,
    EXECUTION_ORCHESTRATOR,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    PROMPT_BUILDER,
)
from dipeo.config.llm import PERSON_JOB_MAX_TOKENS, PERSON_JOB_TEMPERATURE
from dipeo.diagram_generated.domain_models import PersonID
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.conversation import Person
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .batch_executor import BatchExecutor
from .conversation_handler import ConversationHandler
from .text_format_handler import TextFormatHandler

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
@requires_services(
    llm_service=(LLM_SERVICE, Required),
    diagram=(DIAGRAM, Required),
    execution_orchestrator=(EXECUTION_ORCHESTRATOR, Required),
    prompt_builder=(PROMPT_BUILDER, Required),
    filesystem_adapter=(FILESYSTEM_ADAPTER, Optional),
)
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    """Handler for executing AI person jobs with conversation memory.

    REFACTORED: This handler now directly contains all execution logic,
    eliminating the separate executor layer for improved simplicity and performance.
    Supports both single person and batch execution modes.
    """

    NODE_TYPE = NodeType.PERSON_JOB.value

    def __init__(self):
        super().__init__()

        # Use cases and utility handlers
        self._text_format_handler = TextFormatHandler()
        self._conversation_handler = ConversationHandler()
        self._batch_executor = BatchExecutor(self._execute_single)

        # Instance variable for debug flag
        self._current_debug = False

        # Will be initialized when filesystem_adapter is available
        self._prompt_loading_use_case = None

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
        """Legacy property for backward compatibility."""
        return self.get_required_services() + self.get_optional_services()

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory, supporting both single and batch execution"

    def validate(self, request: ExecutionRequest[PersonJobNode]) -> str | None:
        """Validate the execution request."""
        node = request.node

        if not node.person:
            return "No person specified"

        # Validate batch configuration
        if getattr(node, "batch", False):
            batch_input_key = getattr(node, "batch_input_key", "items")
            if not batch_input_key:
                return "Batch mode enabled but batch_input_key not specified"

        return None

    async def pre_execute(self, request: ExecutionRequest[PersonJobNode]) -> Envelope | None:
        """Pre-execution hook to check max_iteration limit."""
        node = request.node
        context = request.context

        # Set debug flag for later use
        self._current_debug = False
        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[PersonJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data for person job."""
        node = request.node

        # Phase 5: Consume tokens from incoming edges
        envelope_inputs = self.get_effective_inputs(request, inputs)
        self._envelope_inputs = envelope_inputs
        inputs = envelope_inputs

        # Extract prompt from envelope
        prompt_envelope = self.get_optional_input(inputs, "prompt")
        prompt = None
        if prompt_envelope:
            prompt = prompt_envelope.as_text()
        else:
            # Check for various prompt sources
            has_prompt_file = getattr(node, "prompt_file", None) or getattr(
                node, "first_prompt_file", None
            )
            has_resolved_prompt = getattr(node, "resolved_prompt", None) or getattr(
                node, "resolved_first_prompt", None
            )
            prompt = getattr(node, "default_prompt", None)

            if not prompt and not has_prompt_file and not has_resolved_prompt:
                raise ValueError(
                    f"No prompt provided and no default_prompt, prompt_file, or resolved_prompt configured for node {node.id}"
                )

        # Extract context
        context_data = None
        if context_envelope := self.get_optional_input(inputs, "context"):
            try:
                context_data = context_envelope.as_json()
            except ValueError:
                context_data = context_envelope.as_text()

        # Get conversation state if needed
        conversation_state = None
        if conv_envelope := self.get_optional_input(inputs, "_conversation"):
            conversation_state = conv_envelope.as_conversation()

        # Convert envelope inputs to plain values
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

        # Override with explicit values if provided
        if prompt is not None:
            processed_inputs["prompt"] = prompt
        if context_data is not None:
            processed_inputs["context"] = context_data
        if conversation_state:
            processed_inputs["_conversation"] = conversation_state

        return processed_inputs

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[PersonJobNode]) -> Any:
        """Execute person job with prepared inputs."""
        node = request.node
        request.inputs = inputs

        # Initialize prompt loading use case if filesystem_adapter is available
        if self._filesystem_adapter and not self._prompt_loading_use_case:
            self._prompt_loading_use_case = PromptLoadingUseCase(self._filesystem_adapter)

        # Check if batch mode is enabled
        if getattr(node, "batch", False):
            logger.info(f"Executing PersonJobNode {node.id} in batch mode")
            return await self._batch_executor.execute_batch(request)
        else:
            return await self._execute_single(request)

    # ==============================================================================
    # SINGLE EXECUTION LOGIC (merged from SinglePersonJobExecutor)
    # ==============================================================================

    async def _execute_single(self, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Execute the person job for a single person (merged from SinglePersonJobExecutor)."""
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        inputs = request.inputs

        # Direct typed access to person_id
        person_id = node.person
        execution_count = context.state.get_node_execution_count(node.id)

        # Get or create person using the orchestrator
        if not self._execution_orchestrator:
            raise ValueError(f"ExecutionOrchestrator not available for person {person_id}")

        person = self._execution_orchestrator.get_or_create_person(
            PersonID(person_id), diagram=self._diagram
        )

        # Extract values from Envelope objects for template processing
        extracted_inputs = {}
        for key, value in inputs.items():
            if hasattr(value, "body"):  # It's an Envelope
                body = value.body
                # Filter out internal metadata from conversation outputs
                if isinstance(body, dict) and "llm_usage" in body:
                    # Create a copy without llm_usage
                    body = {k: v for k, v in body.items() if k != "llm_usage"}
                extracted_inputs[key] = body
            else:
                extracted_inputs[key] = value
        transformed_inputs = extracted_inputs

        # Handle conversation inputs
        has_conversation_input = self._conversation_handler.has_conversation_input(
            transformed_inputs
        )
        if has_conversation_input:
            messages_to_add = self._conversation_handler.load_conversation_from_inputs(
                transformed_inputs, str(person.id)
            )
            if messages_to_add and hasattr(self._execution_orchestrator, "add_message"):
                for msg in messages_to_add:
                    self._execution_orchestrator.add_message(
                        msg, execution_id=trace_id, node_id=str(node.id)
                    )

        # Get all messages from conversation repository
        all_messages = (
            self._execution_orchestrator.get_conversation().messages
            if hasattr(self._execution_orchestrator, "get_conversation")
            else []
        )

        # Load prompts
        prompt_content = node.default_prompt
        first_only_content = node.first_only_prompt

        # Check for pre-resolved prompts
        if hasattr(node, "resolved_first_prompt") and node.resolved_first_prompt:
            first_only_content = node.resolved_first_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved first prompt")

        if hasattr(node, "resolved_prompt") and node.resolved_prompt:
            prompt_content = node.resolved_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved default prompt")

        # Memory selection configuration
        memorize_to = getattr(node, "memorize_to", None)
        at_most = getattr(node, "at_most", None)
        ignore_person = getattr(node, "ignore_person", None)

        # Prepare template values
        input_values = self._prompt_builder.prepare_template_values(transformed_inputs)
        logger.debug(f"[PersonJob] input_values keys after prepare: {list(input_values.keys())}")

        # Build template context from inputs only
        template_values = context.build_template_context(inputs=input_values, globals_win=True)

        # Build prompt with template substitution
        built_prompt = self._prompt_builder.build(
            prompt=prompt_content,
            template_values=template_values,
            first_only_prompt=first_only_content,
            execution_count=execution_count,
        )

        # Log template warning if needed
        if "{{" in (built_prompt or ""):
            logger.warning(
                f"[PersonJob {node.label or node.id}] Template variables may not be substituted! Found '{{{{' in built prompt"
            )

        # Skip if no prompt
        if not built_prompt:
            logger.warning(f"Skipping execution for person {person_id} - no prompt available")
            return EnvelopeFactory.create(body="", produced_by=str(node.id), trace_id=trace_id)

        # Prepare LLM call arguments
        complete_kwargs = {
            "prompt": built_prompt,
            "llm_service": self._llm_service,
            "from_person_id": "system",
            "temperature": PERSON_JOB_TEMPERATURE,
            "max_tokens": PERSON_JOB_MAX_TOKENS,
        }

        # Claude Code specific execution options
        # Pass trace_id for workspace directory creation in claude-code
        complete_kwargs["trace_id"] = trace_id

        # Handle tools configuration
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

        # Handle text_format configuration
        pydantic_model = self._text_format_handler.get_pydantic_model(node)
        if pydantic_model:
            complete_kwargs["text_format"] = pydantic_model

        # Build task preview for memory selection
        task_preview = None
        if memorize_to or at_most:
            task_preview_raw = prompt_content or first_only_content or ""
            task_preview = self._prompt_builder.build(
                prompt=task_preview_raw,
                template_values=template_values,
                first_only_prompt=None,
                execution_count=execution_count,
            )

        # Execute LLM call with memory selection
        result, incoming_msg, response_msg, selected_messages = await person.complete_with_memory(
            all_messages=all_messages,
            memorize_to=memorize_to,
            ignore_person=ignore_person,
            at_most=at_most,
            prompt_preview=task_preview,
            **complete_kwargs,
        )

        # GOLDFISH mode is handled by memory strategy returning empty list
        # Add messages to conversation
        if hasattr(self._execution_orchestrator, "add_message"):
            self._execution_orchestrator.add_message(
                incoming_msg, execution_id=trace_id, node_id=str(node.id)
            )
            self._execution_orchestrator.add_message(
                response_msg, execution_id=trace_id, node_id=str(node.id)
            )

        # Build and return output
        return self._build_single_node_output(
            result=result,
            person=person,
            node=node,
            diagram=self._diagram,
            model=person.llm_config.model,
            trace_id=trace_id,
            selected_messages=selected_messages,
        )

    def _build_single_node_output(
        self,
        result: Any,
        person: Person,
        node: PersonJobNode,
        diagram: Any,
        model: str,
        trace_id: str = "",
        selected_messages: list | None = None,
    ) -> Envelope:
        """Build node output with envelope support for single execution."""
        # Extract LLM usage
        llm_usage = None
        if hasattr(result, "llm_usage") and result.llm_usage:
            llm_usage = result.llm_usage

        # Get person and conversation IDs
        person_id = str(person.id) if person.id else None
        conversation_id = None

        # Build all representations
        text_repr = self._extract_text(result)
        object_repr = self._extract_object(result, node)

        # Lazy evaluation for conversation
        conversation_repr = None
        if self._any_edge_needs_conversation(node.id, diagram):
            conversation_repr = self._build_conversation_repr(
                person, selected_messages, model, result
            )

        # Determine primary body
        primary_envelope = self._determine_primary_envelope(
            node,
            diagram,
            text_repr,
            object_repr,
            conversation_repr,
            person_id,
            conversation_id,
            model,
            llm_usage,
            trace_id,
            selected_messages,
        )

        # Add all representations
        representations = {"text": text_repr}
        if object_repr is not None:
            representations["object"] = object_repr
        if conversation_repr is not None:
            representations["conversation"] = conversation_repr

        return primary_envelope.with_meta(representations=representations)

    # ==============================================================================
    # HELPER METHODS (shared by both single and batch execution)
    # ==============================================================================

    def _extract_text(self, result):
        """Extract text representation from result."""
        if hasattr(result, "content"):
            return result.content
        elif hasattr(result, "text"):
            return result.text
        return str(result)

    def _extract_object(self, result, node):
        """Extract structured object if text_format was used."""
        has_text_format = (hasattr(node, "text_format") and node.text_format) or (
            hasattr(node, "text_format_file") and node.text_format_file
        )

        if has_text_format:
            return self._text_format_handler.process_structured_output(result, True)
        return None

    def _build_conversation_repr(self, person, selected_messages, model, result):
        """Build conversation representation."""
        if selected_messages is not None:
            messages = selected_messages
        else:
            all_conv_messages = (
                self._execution_orchestrator.get_conversation().messages
                if hasattr(self._execution_orchestrator, "get_conversation")
                else []
            )
            # Filter messages relevant to this person
            messages = [
                msg
                for msg in all_conv_messages
                if msg.from_person_id == person.id or msg.to_person_id == person.id
            ]

        return {
            "messages": messages,
            "last_message": messages[-1] if messages else None,
            "person_id": str(person.id),
            "model": model,
        }

    def _any_edge_needs_conversation(self, node_id, diagram):
        """Check if any outgoing edge needs conversation representation."""
        from dipeo.diagram_generated.enums import ContentType

        if not diagram or not hasattr(diagram, "get_outgoing_edges"):
            return False

        edges = diagram.get_outgoing_edges(node_id)
        return any(
            hasattr(edge, "content_type") and edge.content_type == ContentType.CONVERSATION_STATE
            for edge in edges
        )

    def _determine_primary_envelope(
        self,
        node,
        diagram,
        text_repr,
        object_repr,
        conversation_repr,
        person_id,
        conversation_id,
        model,
        llm_usage,
        trace_id,
        selected_messages=None,
    ):
        """Create envelope using natural data output pattern."""
        # Determine the natural body content
        natural_body = text_repr  # Default to text

        # Check if conversation output is needed
        if self._conversation_handler.needs_conversation_output(str(node.id), diagram):
            natural_body = (
                conversation_repr if conversation_repr else {"messages": [], "last_message": None}
            )
        # Check if structured data is available
        elif object_repr is not None:
            natural_body = object_repr

        # Prepare memory selection info for metadata
        memory_selection = None
        if selected_messages is not None:
            # Get all messages from conversation to determine the total count
            all_messages = (
                self._execution_orchestrator.get_conversation().messages
                if hasattr(self._execution_orchestrator, "get_conversation")
                else []
            )
            total_available = len(all_messages) if all_messages else 0
            memory_selection = {
                "selected_count": len(selected_messages),
                "total_messages": total_available,
                "criteria": getattr(node, "memorize_to", None),
                "at_most": getattr(node, "at_most", None),
            }

        # Use EnvelopeFactory.create() with auto-detection
        envelope = EnvelopeFactory.create(
            body=natural_body,
            produced_by=str(node.id),
            trace_id=trace_id,
            meta={
                "person_id": person_id,
                "conversation_id": conversation_id,
                "model": model,
                "llm_usage": llm_usage.model_dump() if llm_usage else None,
                "memory_selection": memory_selection,
                "preview": text_repr[:200] if text_repr else None,
                "is_structured": object_repr is not None,
            },
        )

        return envelope

    def serialize_output(self, result: Any, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Serialize person job result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""

        # Check if batch mode
        if getattr(node, "batch", False):
            # Batch result is already an Envelope from BatchExecutor
            if isinstance(result, Envelope):
                return result
            else:
                # Fallback for unexpected format
                if hasattr(result, "value"):
                    output_envelope = EnvelopeFactory.create(
                        body=result.value, produced_by=node.id, trace_id=trace_id
                    ).with_meta(batch_mode=True, person_id=node.person)
                else:
                    output_envelope = EnvelopeFactory.create(
                        body=str(result), produced_by=node.id, trace_id=trace_id
                    )
                return output_envelope
        else:
            # Single execution already returns an Envelope from _execute_single
            if isinstance(result, Envelope):
                return result
            else:
                # Fallback for unexpected result format
                logger.warning(f"Unexpected result type from _execute_single: {type(result)}")
                output_envelope = EnvelopeFactory.create(
                    body=str(result), produced_by=node.id, trace_id=trace_id
                )
                return output_envelope

    async def on_error(
        self, request: ExecutionRequest[PersonJobNode], error: Exception
    ) -> Envelope | None:
        """Handle errors gracefully with envelope output."""
        trace_id = request.execution_id or ""

        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return EnvelopeFactory.create(
                body={"error": f"ValidationError: {error}", "type": "ValueError"},
                produced_by=request.node.id,
                trace_id=trace_id,
            )

        # For other errors, log them
        logger.error(f"Error executing person job: {error}")
        return EnvelopeFactory.create(
            body={"error": str(error), "type": error.__class__.__name__},
            produced_by=request.node.id,
            trace_id=trace_id,
        )

    def post_execute(self, request: ExecutionRequest[PersonJobNode], output: Envelope) -> Envelope:
        """Post-execution hook to log execution details and emit tokens."""
        # Log execution details if in debug mode
        if self._current_debug:
            is_batch = getattr(request.node, "batch", False)
            if is_batch:
                batch_info = output.value if hasattr(output, "value") else {}
                total = batch_info.get("total_items", 0)
                successful = batch_info.get("successful", 0)
                logger.debug(f"Batch person job completed: {successful}/{total} successful")
            else:
                logger.debug(f"Person job completed for {request.node.person}")

        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
