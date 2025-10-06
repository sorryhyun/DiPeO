"""Intelligent memory selection for conversation management.

This module provides LLM-based intelligent memory selection with
scoring and deduplication capabilities.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.config.memory import (
    MEMORY_CONTENT_KEY_LENGTH,
    MEMORY_DECAY_FACTOR,
    MEMORY_HARD_CAP,
    MEMORY_SCORING_WEIGHTS,
    MEMORY_WORD_OVERLAP_THRESHOLD,
)
from dipeo.diagram_generated.domain_models import Message, PersonID
from dipeo.infrastructure.timing.context import atime_phase, time_phase

if TYPE_CHECKING:
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort


@dataclass
class MemoryConfig:
    """Configuration for memory selection behavior."""

    hard_cap: int = MEMORY_HARD_CAP
    decay_factor: int = MEMORY_DECAY_FACTOR
    word_overlap_threshold: float = MEMORY_WORD_OVERLAP_THRESHOLD
    default_weights: dict[str, float] = field(default_factory=lambda: MEMORY_SCORING_WEIGHTS.copy())


class IntelligentMemoryStrategy:
    """Memory strategy using LLM-based intelligent selection with scoring and deduplication."""

    def __init__(
        self,
        llm_service: Optional["LLMServicePort"] = None,
        config: MemoryConfig | None = None,
        person_repository: Any = None,
    ):
        self.config = config or MemoryConfig()
        self.llm_service = llm_service
        self.person_repository = person_repository

    async def select_memories(
        self,
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        ignore_person: str | None,
        at_most: int | None,
        **kwargs,
    ) -> list[Message] | None:
        if not memorize_to or not memorize_to.strip():
            return None

        if memorize_to.strip().upper() == "GOLDFISH":
            return []

        if not self.llm_service:
            return None

        # Extract execution_id for timing (if available)
        exec_id = kwargs.get("execution_id", "")
        person_id = kwargs.pop("person_id", PersonID("system"))
        strategy_id = "memory_strategy"

        # Phase 1: Filtering
        with time_phase(exec_id, strategy_id, "filtering"):
            filtered_candidates = self._filter_messages(candidate_messages, ignore_person)
            print(f"[Memory] After filtering: {len(filtered_candidates)} messages (from {len(candidate_messages)} original)")

        # Phase 2: Deduplication
        with time_phase(exec_id, strategy_id, "deduplication"):
            unique_messages, frequencies = self._deduplicate_messages(filtered_candidates)
            print(f"[Memory] After deduplication: {len(unique_messages)} unique messages")

        # Phase 3: Scoring
        with time_phase(exec_id, strategy_id, "scoring"):
            scored_messages = self._score_and_rank_messages(
                unique_messages, frequencies, datetime.now()
            )
            print(f"[Memory] After scoring: {len(scored_messages)} scored messages")

        top_candidates = [msg for msg, score in scored_messages[: self.config.hard_cap]]
        print(f"[Memory] Top candidates (hard_cap={self.config.hard_cap}): {len(top_candidates)} messages")

        person_name = None

        # Get person's LLM config and name if available
        if self.person_repository:
            try:
                person = self.person_repository.get(person_id)
                llm_config = person.llm_config
                model = llm_config.model
                api_key_id = (
                    llm_config.api_key_id.value
                    if hasattr(llm_config.api_key_id, "value")
                    else str(llm_config.api_key_id)
                )
                service_name = (
                    llm_config.service.value
                    if hasattr(llm_config.service, "value")
                    else str(llm_config.service)
                )
                # Get the person name
                person_name = person.name or str(person_id)
            except (KeyError, AttributeError):
                # Fallback to defaults if person not found
                model = kwargs.get("model", "gpt-5-nano-2025-08-07")
                api_key_id = kwargs.get("api_key_id", "APIKEY_52609F")
                service_name = kwargs.get("service_name", "openai")
                person_name = str(person_id)
        else:
            # Use kwargs or defaults
            model = kwargs.get("model", "gpt-5-nano-2025-08-07")
            api_key_id = kwargs.get("api_key_id", "APIKEY_52609F")
            service_name = kwargs.get("service_name", "openai")
            person_name = str(person_id)

        # Phase 4: LLM Selection
        async with atime_phase(exec_id, strategy_id, "llm_selection"):
            output = await self.llm_service.complete_memory_selection(
                candidate_messages=list(top_candidates),
                task_preview=prompt_preview,
                criteria=memorize_to,
                at_most=at_most,
                model=model,
                api_key_id=api_key_id,
                service_name=service_name,
                person_name=person_name,
                **kwargs,
            )

        # Use the structured output directly
        if not output:
            return None

        # If no message IDs were selected, return empty list (not None)
        # This tells the caller that selection was performed but nothing matched
        if not output.message_ids:
            return []

        idset = set(output.message_ids)
        return [m for m in filtered_candidates if m.id and m.id in idset]

    def _filter_messages(
        self, messages: Sequence[Message], ignore_person: str | None
    ) -> list[Message]:
        ignored_persons = set()
        if ignore_person:
            ignored_persons = {p.strip() for p in ignore_person.split(",") if p.strip()}

        filtered = []
        for msg in messages:
            if msg.from_person_id and ".__selector" in str(msg.from_person_id):
                continue
            if msg.to_person_id and ".__selector" in str(msg.to_person_id):
                continue

            if ignored_persons and msg.from_person_id:
                if str(msg.from_person_id) in ignored_persons:
                    continue

            filtered.append(msg)

        return filtered

    def _deduplicate_messages(
        self, messages: Sequence[Message]
    ) -> tuple[list[Message], dict[str, int]]:
        unique_messages = []
        frequencies = {}
        seen_contents = []

        for message in messages:
            if not getattr(message, "id", None):
                continue

            content_key = (message.content or "")[:MEMORY_CONTENT_KEY_LENGTH].strip()

            is_duplicate = False
            for seen_content, seen_msg in seen_contents:
                if self._calculate_word_overlap(content_key, seen_content):
                    frequencies[seen_msg.id] = frequencies.get(seen_msg.id, 1) + 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_messages.append(message)
                frequencies[message.id] = 1
                seen_contents.append((content_key, message))

        return unique_messages, frequencies

    def _calculate_word_overlap(self, text1: str, text2: str) -> bool:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return text1 == text2

        intersection = len(words1 & words2)
        smaller_set = min(len(words1), len(words2))

        return (intersection / smaller_set) >= self.config.word_overlap_threshold

    def _score_and_rank_messages(
        self,
        messages: Sequence[Message],
        frequencies: dict[str, int],
        current_time: datetime,
    ) -> list[tuple[Message, float]]:
        scored_messages = []

        for msg in messages:
            if not getattr(msg, "id", None):
                continue

            score = self._score_message(msg, frequencies.get(msg.id, 1), current_time)
            scored_messages.append((msg, score))

        scored_messages.sort(key=lambda x: x[1], reverse=True)
        return scored_messages

    def _score_message(
        self,
        message: Message,
        frequency_count: int,
        current_time: datetime,
    ) -> float:
        weights = self.config.default_weights
        scores = {}

        if message.timestamp and current_time:
            try:
                msg_time = datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
                age_seconds = (current_time - msg_time).total_seconds()
                scores["recency"] = 100 * math.exp(-age_seconds / self.config.decay_factor)
            except (ValueError, AttributeError):
                scores["recency"] = 50
        else:
            scores["recency"] = 50

        scores["frequency"] = min(100, 30 + (frequency_count - 1) * 20)

        if message.from_person_id == PersonID("system"):
            scores["frequency"] = min(100, scores["frequency"] + 30)

        total_score = sum(scores.get(factor, 0) * weight for factor, weight in weights.items())

        return total_score
