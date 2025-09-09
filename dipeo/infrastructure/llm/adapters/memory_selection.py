"""LLM-based memory selection implementation."""

import json
import logging
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from dipeo.config.llm import MEMORY_SELECTION_MAX_TOKENS
from dipeo.config.memory import (
    MEMORY_CONTENT_SNIPPET_LENGTH,
    MEMORY_CRITERIA_MAX_LENGTH,
    MEMORY_TASK_PREVIEW_MAX_LENGTH,
)
from dipeo.config.services import LLMServiceName, normalize_service_name
from dipeo.diagram_generated.domain_models import Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.brain import MemorySelectionConfig

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )

logger = logging.getLogger(__name__)


class LLMMemorySelectionAdapter:
    """LLM-based adapter for memory selection.

    This adapter uses an LLM to intelligently select relevant memories
    based on natural language criteria.

    Implements the MemorySelectionPort protocol.
    """

    def __init__(
        self, orchestrator: "ExecutionOrchestrator", config: MemorySelectionConfig | None = None
    ):
        self._orchestrator = orchestrator
        self._facet_cache: dict[str, Person] = {}
        self._config = config or MemorySelectionConfig()

    def _selector_id(self, person_id: PersonID, service: str | None = None) -> PersonID:
        svc = normalize_service_name(service) if service else ""
        suffix = f"::{svc}" if svc else ""
        return PersonID(f"{person_id!s}.__selector{suffix}")

    def _selector_system_prompt(
        self,
        base_prompt: str | None,
        person_name: str | None = None,
        llm_service: str | None = None,
    ) -> str:
        base = (base_prompt or "").strip()

        # Claude Code adapter provides its own MEMORY_SELECTION_PROMPT when execution_phase="memory_selection"
        # The MEMORY_SELECTION_PROMPT already includes YOUR NAME placeholder that will be formatted
        if llm_service and normalize_service_name(llm_service) == LLMServiceName.CLAUDE_CODE.value:
            # Pass the person name in a special format that the adapter will recognize
            # The adapter will extract this and format it into the MEMORY_SELECTION_PROMPT
            if person_name:
                # Use a marker that won't be duplicated in the final prompt
                return (
                    f"YOUR NAME: {person_name}\n\n{base}" if base else f"YOUR NAME: {person_name}"
                )
            return base

        # For other adapters (OpenAI, Anthropic, Google, etc.), we need to provide instructions
        # Start with YOUR NAME if provided
        name_prefix = f"YOUR NAME: {person_name}\n\n" if person_name else ""

        return (
            name_prefix + (base + "\n\n" if base else "") + "You are in MEMORY SELECTION MODE.\n"
            "- Input: a candidate list of prior messages with their IDs, "
            "the upcoming task preview, and a natural-language selection criteria.\n"
            '- Output: a pure JSON array of message IDs to keep (e.g., ["m1","m7"]). '
            "No extra text.\n"
            "- Preserve system messages is handled by the caller; do not re-list them.\n"
            "- IMPORTANT: Do NOT select messages whose content is already included in or duplicated by "
            "the task preview. Avoid redundancy.\n"
            "- When a CONSTRAINT specifies maximum messages, respect it strictly and select "
            "the MOST relevant messages within that limit.\n"
            "- Favor precision over recall; choose the smallest set that satisfies the criteria.\n"
            "- If uncertain, return an empty array."
        )

    def _get_or_create_selector_facet(
        self, person_id: PersonID, llm_service: str | None = None
    ) -> Person:
        # Use the provided llm_service or fall back; normalize service name
        base_person = self._orchestrator.get_person(person_id)
        llm = base_person.llm_config

        # Handle case where llm_service is an object (LLMInfraService) instead of string
        if llm_service and isinstance(llm_service, str):
            raw_service = llm_service
        else:
            # Fall back to the person's configured service
            # Use .value to get the enum value, not str() which returns the full representation
            raw_service = llm.service.value if hasattr(llm.service, "value") else str(llm.service)

        service_str = normalize_service_name(raw_service)

        sid = self._selector_id(person_id, service_str)
        persons = self._orchestrator.get_all_persons()
        if sid in persons:
            return persons[sid]

        # Get person name for system prompt
        base_person = self._orchestrator.get_person(person_id)
        person_name = base_person.name or str(person_id)

        facet_cfg = PersonLLMConfig(
            service=service_str,
            model=llm.model,
            api_key_id=llm.api_key_id,
            system_prompt=self._selector_system_prompt(llm.system_prompt, person_name, service_str),
            prompt_file=None,
        )
        facet = self._orchestrator.get_or_create_person(
            person_id=sid, name="Selector Facet", llm_config=facet_cfg
        )
        # The selector facet uses empty message list so no filter needed
        # It only responds to the specific selection prompt we send it
        self._facet_cache[str(sid)] = facet
        return facet

    async def select_memories(
        self,
        *,
        person_id: PersonID,
        candidate_messages: Sequence[Message],
        task_preview: str,
        criteria: str,
        at_most: int | None = None,
        **kwargs,
    ) -> list[str]:
        """Select relevant message IDs based on criteria using LLM.

        Args:
            person_id: The person for whom we're selecting memories
            candidate_messages: Messages to select from
            task_preview: Preview of the upcoming task for context
            criteria: Selection criteria (natural language)
            at_most: Maximum number of messages to select
            **kwargs: Additional parameters (llm_service, preprocessed, etc.)

        Returns:
            List of selected message IDs
        """
        if not criteria or not criteria.strip():
            return []

        # Extract optional parameters from kwargs
        llm_service = kwargs.get("llm_service")
        preprocessed = kwargs.get("preprocessed", False)

        facet = self._get_or_create_selector_facet(person_id, llm_service)

        # Build a compact selection prompt
        preview = (task_preview or "")[:MEMORY_TASK_PREVIEW_MAX_LENGTH]
        crit = (criteria or "").strip()[:MEMORY_CRITERIA_MAX_LENGTH]

        # Create listing from candidate messages
        # If preprocessed=True, messages are already deduplicated, scored, and sorted
        lines = []

        # Get base person for name resolution
        base_person = self._orchestrator.get_person(person_id)

        for _i, msg in enumerate(candidate_messages):
            if not getattr(msg, "id", None):
                continue

            # Get content snippet
            content_key = (msg.content or "")[:MEMORY_CONTENT_SNIPPET_LENGTH].strip()
            snippet = content_key.replace("\n", " ")

            # Get sender name/label
            if msg.from_person_id == PersonID("system"):
                sender_label = "system"
            elif msg.from_person_id == person_id:
                sender_label = base_person.name
            else:
                sender_label = str(msg.from_person_id)
                if hasattr(self._orchestrator, "get_all_persons"):
                    persons = self._orchestrator.get_all_persons()
                    from_person_id = PersonID(str(msg.from_person_id))
                    if from_person_id in persons:
                        sender_label = persons[from_person_id].name or str(msg.from_person_id)

            lines.append(f"- {msg.id} ({sender_label}): {snippet}")

        listing = "\n".join(lines)

        # Build prompt with at_most constraint if specified
        constraint_text = ""
        if at_most and at_most > 0:
            constraint_text = f"\nCONSTRAINT: Select at most {int(at_most)} messages that best match the criteria.\n"

        prompt = (
            "CANDIDATE MESSAGES (id (sender): snippet):\n"
            f"{listing}\n\n===\n\n"
            f"TASK PREVIEW:\n===\n\n{preview}\n\n===\n\n"
            f"CRITERIA:\n{crit}\n\n"
            f"{constraint_text}"
            "IMPORTANT: Exclude messages that duplicate content already in the task preview.\n"
            "Return a JSON array of message IDs only."
        )

        # Execute using person's complete method directly
        # Pass empty messages list since selector gets all info in the prompt
        complete_kwargs = {
            "prompt": prompt,
            "all_messages": [],  # Empty list - selector doesn't need conversation context
            "llm_service": llm_service,
            "temperature": 0,
            "max_tokens": MEMORY_SELECTION_MAX_TOKENS,
        }

        # Always pass phase; adapters that care will use it
        complete_kwargs["execution_phase"] = "memory_selection"

        result, incoming_msg, response_msg = await facet.complete(**complete_kwargs)

        # Add messages to conversation if orchestrator supports it
        if hasattr(self._orchestrator, "add_message"):
            self._orchestrator.add_message(incoming_msg, "memory_selection", "memory_selector")
            self._orchestrator.add_message(response_msg, "memory_selection", "memory_selector")

        # Robust parse with multiple fallback strategies
        text = getattr(result, "content", getattr(result, "text", "")) or ""

        try:
            # Try 1: Direct JSON parsing
            data = json.loads(text)

            # Handle both dict format {"message_ids": [...]} and direct list format [...]
            if isinstance(data, dict) and "message_ids" in data:
                # Dictionary format with message_ids key
                ids = [str(x) for x in data["message_ids"] if x]
            elif isinstance(data, list):
                # Direct list format (from structured output)
                ids = [str(x) for x in data if x]
            else:
                # Unexpected format
                logger.warning(
                    f"[MemorySelector] Unexpected data format: {type(data)}, value: {data}"
                )
                ids = []

        except Exception:
            # Try 2: Extract JSON array using regex
            try:
                m = re.search(r"\[.*?]", text, re.S)
                if m:
                    data = json.loads(m.group(0))
                    ids = [str(x) for x in data if x]
                else:
                    raise ValueError("No JSON array found")
            except Exception:
                # Try 3: String matching fallback - find any IDs that match our candidate IDs
                # Build a set of all valid message IDs from candidates
                valid_ids = set()
                for msg in candidate_messages:
                    if hasattr(msg, "id") and msg.id:
                        valid_ids.add(str(msg.id))

                # Find all valid IDs mentioned in the response text
                ids = []
                for valid_id in valid_ids:
                    # Check if ID appears in the text (with word boundaries to avoid partial matches)
                    # Look for the ID surrounded by non-alphanumeric characters
                    pattern = r"(?:^|[^a-zA-Z0-9])" + re.escape(valid_id) + r"(?:[^a-zA-Z0-9]|$)"
                    if re.search(pattern, text):
                        ids.append(valid_id)

                if ids:
                    logger.info(
                        f"[MemorySelector] Extracted {len(ids)} IDs via string matching: {ids}"
                    )
                else:
                    # No IDs found - treat as empty selection
                    ids = []
        logger.info(f"[MemorySelector] Extracted memory ids: {ids}")
        return ids
