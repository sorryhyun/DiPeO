"""Specialized completion handlers for memory selection and decision evaluation."""

import json
from typing import Any, Callable

from dipeo.config.llm import DECISION_EVALUATION_MAX_TOKENS, MEMORY_SELECTION_MAX_TOKENS
from dipeo.config.memory import MEMORY_CONTENT_SNIPPET_LENGTH, MEMORY_TASK_PREVIEW_MAX_LENGTH
from dipeo.diagram_generated import ChatResult
from dipeo.diagram_generated.domain_models import PersonID
from dipeo.diagram_generated.enums import ExecutionPhase
from dipeo.domain.base.mixins import LoggingMixin
from dipeo.infrastructure.llm.drivers.decision_parser import DecisionParser
from dipeo.infrastructure.llm.drivers.types import DecisionOutput, MemorySelectionOutput


class CompletionHandlers(LoggingMixin):
    """Handles specialized completion tasks: memory selection and decision evaluation."""

    def __init__(
        self,
        complete_fn: Callable,
        decision_parser: DecisionParser,
    ):
        super().__init__()
        self._complete_fn = complete_fn
        self._decision_parser = decision_parser

    async def complete_memory_selection(
        self,
        candidate_messages: list[Any],
        task_preview: str,
        criteria: str,
        at_most: int | None,
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> MemorySelectionOutput:
        """Direct memory selection without domain adapter."""
        if not criteria or not criteria.strip():
            return MemorySelectionOutput([])

        # Build memory listing
        lines = []
        for msg in candidate_messages:
            if not getattr(msg, "id", None):
                continue

            content_snippet = (msg.content or "")[:MEMORY_CONTENT_SNIPPET_LENGTH].strip()
            snippet = content_snippet.replace("\n", " ")

            # Determine sender label
            if hasattr(msg, "from_person_id"):
                if msg.from_person_id == PersonID("system"):
                    sender_label = "system"
                else:
                    sender_label = str(msg.from_person_id)
            else:
                sender_label = "unknown"

            lines.append(f"- {msg.id} ({sender_label}): {snippet}")

        listing = "\n".join(lines)
        preview = (task_preview or "")[:MEMORY_TASK_PREVIEW_MAX_LENGTH]

        constraint_text = ""
        if at_most and at_most > 0:
            constraint_text = f"\nCONSTRAINT: Select at most {int(at_most)} messages that best match the criteria.\n"

        user_prompt = (
            "CANDIDATE MESSAGES (id (sender): snippet):\n"
            f"{listing}\n\n===\n\n"
            f"TASK PREVIEW:\n===\n\n{preview}\n\n===\n\n"
            f"CRITERIA:\n{criteria}\n\n"
            f"{constraint_text}"
            "IMPORTANT: Exclude messages that duplicate content already in the task preview.\n"
            "Return a JSON array of message IDs only."
        )

        messages = [{"role": "user", "content": user_prompt}]

        # Remove parameters that are not needed for the complete() method
        kwargs.pop("preprocessed", None)
        kwargs.pop("llm_service", None)
        kwargs.pop("person_id", None)

        result = await self._complete_fn(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            execution_phase=ExecutionPhase.MEMORY_SELECTION,
            temperature=0,
            max_tokens=MEMORY_SELECTION_MAX_TOKENS,
            **kwargs,
        )

        # Parse MemorySelectionOutput from text response
        ids = []
        if result.text:
            try:
                parsed = json.loads(result.text)
                if isinstance(parsed, dict) and "message_ids" in parsed:
                    ids = parsed["message_ids"]
                elif isinstance(parsed, list):
                    ids = parsed
                else:
                    self.log_warning(f"Unexpected memory selection format: {type(parsed)}")
                    ids = []
            except (json.JSONDecodeError, ValueError) as e:
                self.log_warning(f"Failed to parse memory selection JSON: {e}")
                ids = []
        else:
            self.log_warning("Memory selection result.text is empty")

        output = MemorySelectionOutput(message_ids=ids)
        self.log_info(
            f"Memory selection extracted {len(output.message_ids)} message IDs from candidates: {[msg.id for msg in candidate_messages[:3]]}"
        )
        return output

    async def complete_decision(
        self,
        prompt: str,
        context: dict[str, Any],
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> DecisionOutput:
        """Direct decision evaluation without domain adapter."""
        if not prompt or not prompt.strip():
            return DecisionOutput(decision=False)

        # Build complete prompt with context
        complete_prompt = prompt
        if context:
            # Extract content to evaluate from context
            content_to_evaluate = None

            if "default" in context:
                content_to_evaluate = context["default"]
            elif "generated_output" in context:
                content_to_evaluate = context["generated_output"]
            else:
                # Filter out execution context keys
                context_keys = {
                    "current_index",
                    "last_index",
                    "iteration_count",
                    "loop_index",
                    "execution_count",
                    "node_execution_count",
                }
                filtered = {
                    k: v
                    for k, v in context.items()
                    if not k.startswith("branch[")
                    and not k.endswith("_last_increment_at")
                    and k not in context_keys
                }
                content_to_evaluate = filtered if filtered else context

            # Add content to prompt
            if content_to_evaluate is not None:
                if isinstance(content_to_evaluate, str):
                    complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate}\n--- End of Content ---"
                else:
                    try:
                        content_json = json.dumps(content_to_evaluate, indent=2)
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_json}\n--- End of Content ---"
                    except (TypeError, ValueError):
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate!s}\n--- End of Content ---"

        messages = [{"role": "user", "content": complete_prompt}]

        # Remove any unexpected parameters
        for key in list(kwargs.keys()):
            kwargs.pop(key, None)

        result = await self._complete_fn(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            execution_phase=ExecutionPhase.DECISION_EVALUATION,
            temperature=0,
            max_tokens=DECISION_EVALUATION_MAX_TOKENS,
            **kwargs,
        )

        # Parse DecisionOutput from text response
        response_text = result.text if hasattr(result, "text") else ""
        decision = self._decision_parser.parse_text_decision(response_text)

        output = DecisionOutput(decision=decision)
        self.log_debug(f"Decision evaluation result: {output.decision}")
        return output
