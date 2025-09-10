"""Handler for PersonJobNode - executes AI person jobs with conversation memory.

This refactored version merges the executor logic directly into the handler,
reducing layers of abstraction from 8 to 4-5 as per the simplification plan.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.use_cases import PromptLoadingUseCase
from dipeo.config.execution import BATCH_MAX_CONCURRENT, BATCH_SIZE
from dipeo.config.llm import PERSON_JOB_MAX_TOKENS, PERSON_JOB_TEMPERATURE
from dipeo.diagram_generated.domain_models import PersonID
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.conversation import Person
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .conversation_handler import ConversationHandler
from .text_format_handler import TextFormatHandler

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    """Handler for executing AI person jobs with conversation memory.

    REFACTORED: This handler now directly contains all execution logic,
    eliminating the separate executor layer for improved simplicity and performance.
    Supports both single person and batch execution modes.
    """

    NODE_TYPE = NodeType.PERSON_JOB.value

    # Batch execution defaults
    DEFAULT_MAX_CONCURRENT = BATCH_MAX_CONCURRENT
    DEFAULT_BATCH_SIZE = BATCH_SIZE

    def __init__(self):
        super().__init__()

        # Services (will be set in pre_execute)
        self._llm_service = None
        self._diagram = None
        self._execution_orchestrator = None
        self._prompt_builder = None
        self._filesystem_adapter = None
        self._services_configured = False

        # Use cases and utility handlers
        self._prompt_loading_use_case = None
        self._text_format_handler = TextFormatHandler()
        self._conversation_handler = ConversationHandler()

        # Instance variable for debug flag
        self._current_debug = False

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
        return [
            "llm_service",
            "diagram",
            "execution_orchestrator",
            "prompt_builder",
            "filesystem_adapter",
        ]

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
        """Pre-execution hook to check max_iteration limit and configure services."""
        node = request.node
        context = request.context

        # Set debug flag for later use
        self._current_debug = False

        # Configure services on first execution
        if not self._services_configured:
            from dipeo.application.registry.keys import (
                DIAGRAM,
                EXECUTION_ORCHESTRATOR,
                FILESYSTEM_ADAPTER,
                LLM_SERVICE,
                PROMPT_BUILDER,
            )

            self._llm_service = request.services.resolve(LLM_SERVICE)
            self._diagram = request.services.resolve(DIAGRAM)
            self._execution_orchestrator = request.services.resolve(EXECUTION_ORCHESTRATOR)
            self._prompt_builder = request.services.resolve(PROMPT_BUILDER)
            self._filesystem_adapter = request.services.resolve(FILESYSTEM_ADAPTER)

            # Initialize prompt loading use case with filesystem
            if self._filesystem_adapter:
                self._prompt_loading_use_case = PromptLoadingUseCase(self._filesystem_adapter)

            self._services_configured = True
        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[PersonJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data for person job."""
        node = request.node

        # Phase 5: Consume tokens from incoming edges
        envelope_inputs = self.consume_token_inputs(request, inputs)
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

        # Check if batch mode is enabled
        if getattr(node, "batch", False):
            logger.info(f"Executing PersonJobNode {node.id} in batch mode")
            return await self._execute_batch(request)
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
                extracted_inputs[key] = value.body
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
        elif (
            hasattr(node, "first_prompt_file")
            and node.first_prompt_file
            and self._prompt_loading_use_case
        ):
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(
                self._diagram
            )
            loaded_content = self._prompt_loading_use_case.load_prompt_file(
                node.first_prompt_file, diagram_source_path, node.label or node.id
            )
            if loaded_content:
                first_only_content = loaded_content

        if hasattr(node, "resolved_prompt") and node.resolved_prompt:
            prompt_content = node.resolved_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved default prompt")
        elif hasattr(node, "prompt_file") and node.prompt_file and self._prompt_loading_use_case:
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(
                self._diagram
            )
            loaded_content = self._prompt_loading_use_case.load_prompt_file(
                node.prompt_file, diagram_source_path, node.label or node.id
            )
            if loaded_content:
                prompt_content = loaded_content

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
            "execution_phase": "direct_execution",
        }

        # Claude Code specific execution options
        try:
            from dipeo.diagram_generated.enums import ExecutionPhase
        except Exception:
            from dipeo.diagram_generated.enums import ExecutionPhase  # type: ignore

        try:
            svc_name = (
                person.llm_config.service.value
                if hasattr(person.llm_config.service, "value")
                else str(person.llm_config.service)
            ).lower()
        except Exception:
            svc_name = str(person.llm_config.service).lower()

        complete_kwargs["execution_phase"] = ExecutionPhase.DIRECT_EXECUTION

        if "claude-code" in svc_name:
            import os
            from pathlib import Path

            root = os.getenv(
                "DIPEO_CLAUDE_WORKSPACES", os.path.join(os.getcwd(), ".dipeo", "workspaces")
            )
            workspace_dir = Path(root) / f"exec_{trace_id or 'default'}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            complete_kwargs["cwd"] = str(workspace_dir)

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

        # Handle GOLDFISH mode
        if memorize_to and memorize_to.strip().upper() == "GOLDFISH":
            if hasattr(self._execution_orchestrator, "clear_person_messages"):
                self._execution_orchestrator.clear_person_messages(person.id)

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
        from dataclasses import replace

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
        )

        # Add all representations
        representations = {"text": text_repr}
        if object_repr is not None:
            representations["object"] = object_repr
        if conversation_repr is not None:
            representations["conversation"] = conversation_repr

        return replace(primary_envelope, representations=representations)

    # ==============================================================================
    # BATCH EXECUTION LOGIC (merged from BatchPersonJobExecutor)
    # ==============================================================================

    async def _execute_batch(self, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Execute person job for each item in the batch (merged from BatchPersonJobExecutor)."""
        node = request.node
        trace_id = request.execution_id or ""

        # Get batch configuration
        batch_config = self._get_batch_configuration(node)

        logger.debug(
            f"Batch configuration - key: {batch_config['input_key']}, "
            f"parallel: {batch_config['parallel']}, "
            f"max_concurrent: {batch_config['max_concurrent']}"
        )

        # Extract array from inputs
        batch_items = self._extract_batch_items(request.inputs, batch_config["input_key"])

        if not batch_items:
            return self._create_empty_batch_output(node, batch_config, trace_id)

        logger.info(f"Processing batch of {len(batch_items)} items for person {node.person}")

        # Execute batch items
        if batch_config["parallel"]:
            results, errors = await self._execute_batch_parallel(
                batch_items, request, batch_config["max_concurrent"]
            )
        else:
            results, errors = await self._execute_batch_sequential(batch_items, request)

        # Return batch output
        return self._create_batch_output(
            node=node,
            batch_items=batch_items,
            results=results,
            errors=errors,
            batch_config=batch_config,
            trace_id=trace_id,
        )

    def _get_batch_configuration(self, node: PersonJobNode) -> dict[str, Any]:
        """Extract batch configuration from node."""
        return {
            "input_key": getattr(node, "batch_input_key", "items"),
            "parallel": getattr(node, "batch_parallel", True),
            "max_concurrent": getattr(node, "max_concurrent", self.DEFAULT_MAX_CONCURRENT),
        }

    def _extract_batch_items(
        self, inputs: dict[str, Any] | None, batch_input_key: str
    ) -> list[Any]:
        """Extract batch items from inputs."""
        if not inputs:
            return []

        logger.debug(
            f"Extracting batch items with key '{batch_input_key}' from inputs: {list(inputs.keys())}"
        )

        batch_items = self._find_batch_items_in_inputs(inputs, batch_input_key)

        if batch_items is None:
            logger.warning(f"No batch items found for key '{batch_input_key}'")
            return []

        if not isinstance(batch_items, list):
            logger.warning(
                f"Batch input '{batch_input_key}' is not a list (type: {type(batch_items)}). "
                f"Treating as single item."
            )
            return [batch_items]

        return batch_items

    def _find_batch_items_in_inputs(
        self, inputs: dict[str, Any], batch_input_key: str
    ) -> Any | None:
        """Find batch items in various input structures."""
        # Direct key in inputs
        if batch_input_key in inputs:
            logger.debug("Found batch items at root level")
            return inputs[batch_input_key]

        # Under 'default' key
        if "default" in inputs:
            default_value = inputs["default"]
            if isinstance(default_value, dict) and batch_input_key in default_value:
                logger.debug("Found batch items under 'default'")
                return default_value[batch_input_key]
            if batch_input_key == "default":
                logger.debug("Batch items are the default value itself")
                return default_value
            if isinstance(default_value, dict):
                for key, value in default_value.items():
                    if key == batch_input_key:
                        logger.debug(f"Found batch items in default dict at key '{key}'")
                        return value

        return None

    async def _execute_batch_parallel(
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode], max_concurrent: int
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items in parallel with concurrency control."""
        results = []
        errors = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(batch_item: Any, index: int) -> Any:
            async with semaphore:
                return await self._execute_batch_item(batch_item, index, len(batch_items), request)

        # Create tasks for all items
        tasks = []
        for idx, item in enumerate(batch_items):
            task = execute_with_semaphore(item, idx)
            tasks.append(task)

        # Wait for all tasks to complete
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for idx, result in enumerate(task_results):
            if isinstance(result, Exception):
                error = self._format_batch_error(idx, result, batch_items)
                logger.error(f"Batch item {idx} failed: {error['error']}")
                errors.append(error)
            else:
                results.append(result)

        return results, errors

    async def _execute_batch_sequential(
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially."""
        results = []
        errors = []

        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_batch_item(item, idx, len(batch_items), request)
                results.append(result)
            except Exception as e:
                error = self._format_batch_error(idx, e, batch_items)
                logger.error(f"Error processing batch item {idx}: {error['error']}", exc_info=True)
                errors.append(error)

        return results, errors

    async def _execute_batch_item(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Execute a single item in the batch."""
        node = original_request.node

        # Create item-specific inputs
        item_inputs = self._create_item_inputs(
            item=item, index=index, total=total, original_request=original_request
        )

        # Create a new request for this batch item
        item_request = self._create_item_request(
            node=node, item_inputs=item_inputs, index=index, original_request=original_request
        )

        # Execute using single execution logic
        logger.debug(f"Executing batch item {index + 1}/{total} for person {node.person}")
        result = await self._execute_single(item_request)

        # Format the result
        return self._format_item_result(index, result)

    def _create_item_inputs(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Create inputs for a single batch item."""
        node = original_request.node
        batch_input_key = getattr(node, "batch_input_key", "items")

        item_inputs = {"default": item, "_batch_index": index, "_batch_total": total}

        # Merge with original inputs (excluding the batch array)
        if original_request.inputs:
            for key, value in original_request.inputs.items():
                if key != batch_input_key and key != "default":
                    item_inputs[key] = value

        return item_inputs

    def _create_item_request(
        self,
        node: PersonJobNode,
        item_inputs: dict[str, Any],
        index: int,
        original_request: ExecutionRequest[PersonJobNode],
    ) -> ExecutionRequest[PersonJobNode]:
        """Create an execution request for a single batch item."""
        return ExecutionRequest(
            node=node,
            context=original_request.context,
            inputs=item_inputs,
            services=original_request.services,
            execution_id=f"{original_request.execution_id}_batch_{index}",
            metadata={},
            parent_registry=original_request.parent_registry,
            parent_container=original_request.parent_container,
        )

    def _format_item_result(self, index: int, result: Any) -> dict[str, Any]:
        """Format the result from a single item execution."""
        if hasattr(result, "body"):  # It's an Envelope
            output_value = result.body
            metadata = result.meta if hasattr(result, "meta") else {}
            return {"index": index, "output": output_value, "metadata": metadata}
        else:
            return {"index": index, "output": str(result), "metadata": {}}

    def _format_batch_error(
        self, index: int, error: Exception, batch_items: list[Any]
    ) -> dict[str, Any]:
        """Format error information for batch processing."""
        return {
            "index": index,
            "error": str(error),
            "error_type": type(error).__name__,
            "item": batch_items[index] if index < len(batch_items) else None,
        }

    def _create_empty_batch_output(
        self, node: PersonJobNode, batch_config: dict[str, Any], trace_id: str = ""
    ) -> Envelope:
        """Create an Envelope for empty batch."""
        logger.warning(
            f"Batch mode enabled but no items found for key '{batch_config['input_key']}'"
        )

        empty_result = {
            "total_items": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "errors": None,
        }

        envelope = EnvelopeFactory.create(body=empty_result, produced_by=node.id, trace_id=trace_id)
        envelope = envelope.with_meta(
            batch_mode="empty", batch_parallel=batch_config["parallel"], person_id=node.person
        )

        return envelope

    def _create_batch_output(
        self,
        node: PersonJobNode,
        batch_items: list[Any],
        results: list[Any],
        errors: list[dict[str, Any]],
        batch_config: dict[str, Any],
        trace_id: str = "",
    ) -> Envelope:
        """Create an Envelope containing batch execution results."""
        batch_output = {
            "total_items": len(batch_items),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None,
        }

        envelope = EnvelopeFactory.create(body=batch_output, produced_by=node.id, trace_id=trace_id)

        meta = {
            "batch_mode": "completed",
            "batch_parallel": batch_config["parallel"],
            "total_items": len(batch_items),
            "successful": len(results),
            "failed": len(errors),
            "person_id": node.person,
        }
        envelope = envelope.with_meta(**meta)

        return envelope

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
            messages = person.get_messages(all_conv_messages)

        return {
            "messages": messages,
            "last_message": messages[-1] if messages else None,
            "person_id": str(person.id),
            "model": model,
            "llm_usage": result.llm_usage.model_dump()
            if hasattr(result, "llm_usage") and result.llm_usage
            else None,
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
            # Batch result is already an Envelope from _execute_batch
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
