import json
import re
from datetime import datetime
from typing import Sequence, Optional, TYPE_CHECKING

from dipeo.diagram_generated.domain_models import Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.brain import (
    MemorySelectionConfig,
    MessageScorer,
    MessageDeduplicator
)

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import ExecutionOrchestrator


class MemorySelector:
    def __init__(self, orchestrator: "ExecutionOrchestrator", config: Optional[MemorySelectionConfig] = None):
        self._orchestrator = orchestrator
        self._facet_cache: dict[str, Person] = {}
        self._config = config or MemorySelectionConfig()
        self._scorer = MessageScorer(self._config)
        self._deduplicator = MessageDeduplicator(self._config)

    def _selector_id(self, base: Person) -> PersonID:
        return PersonID(f"{str(base.id)}.__selector")
    
    
    def _selector_system_prompt(self, base_prompt: Optional[str]) -> str:
        base = (base_prompt or "").strip()
        # Keep the base persona context, then switch into "selector mode"
        return (
            (base + "\n\n" if base else "")
            + "You are in MEMORY SELECTION MODE.\n"
              "- Input: a candidate list of prior messages with their IDs, "
              "the upcoming task preview, and a natural-language selection criteria.\n"
              "- Output: a pure JSON array of message IDs to keep (e.g., [\"m1\",\"m7\"]). "
              "No extra text.\n"
              "- Preserve system messages is handled by the caller; do not re-list them.\n"
              "- IMPORTANT: Do NOT select messages whose content is already included in or duplicated by "
              "the task preview. Avoid redundancy.\n"
              "- When a CONSTRAINT specifies maximum messages, respect it strictly and select "
              "the MOST relevant messages within that limit.\n"
              "- Favor precision over recall; choose the smallest set that satisfies the criteria.\n"
              "- If uncertain, return an empty array."
        )
    
    
    def _get_or_create_selector_facet(self, base: Person) -> Person:
        sid = self._selector_id(base)
        persons = self._orchestrator.get_all_persons()
        if sid in persons:
            return persons[sid]
        
        # Derive LLM config from base
        llm = base.llm_config
        facet_cfg = PersonLLMConfig(
            service=llm.service,
            model=llm.model,
            api_key_id=llm.api_key_id,
            system_prompt=self._selector_system_prompt(llm.system_prompt),
            prompt_file=None,
        )
        facet = self._orchestrator.get_or_create_person(
            person_id=sid, 
            name="Selector Facet", 
            llm_config=facet_cfg
        )
        # The selector facet uses empty message list so no filter needed
        # It only responds to the specific selection prompt we send it
        self._facet_cache[str(sid)] = facet
        return facet
    
    async def select(
        self,
        *,
        person: Person,  # NEW: the base person
        candidate_messages: Sequence[Message],
        task_prompt_preview: str,
        criteria: str,  # String only, comma-separated
        at_most: Optional[int],
        llm_service,  # NEW: pass the llm_service for execute_person_completion
    ) -> list[str]:
        """Return a list of message IDs (strings) to keep.
        
        Args:
            person: The base person for which we're selecting memory
            candidate_messages: Messages to select from
            task_prompt_preview: Preview of the task prompt for context
            criteria: Comma-separated string of selection criteria
            at_most: Maximum number of messages to select
        """
        if not criteria or not criteria.strip():
            return []
        
        facet = self._get_or_create_selector_facet(person)
        
        # Build a compact selection prompt
        # Keep content small; the facet sees ALL_MESSAGES anyway, this gives strong hints
        preview = (task_prompt_preview or "")[:1200]
        crit = (criteria or "").strip()[:750]
        
        # Use domain components to deduplicate and score messages
        current_time = datetime.now()
        
        # Deduplicate messages and get frequencies
        unique_messages, frequencies = self._deduplicator.deduplicate(
            candidate_messages, return_frequencies=True
        )
        
        # Score the unique messages
        scores = self._scorer.score_messages(
            unique_messages,
            frequencies=frequencies,
            current_time=current_time
        )
        
        # Sort unique messages by score
        scored_messages = [
            (msg, scores.get(msg.id, 0.0))
            for msg in unique_messages
            if getattr(msg, "id", None)
        ]
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        
        # Apply hard cap and create listing
        lines = []
        
        for msg, score in scored_messages[:self._config.hard_cap]:
            # Get content snippet
            content_key = (msg.content or "")[:400].strip()
            snippet = content_key.replace("\n", " ")
            
            # Get sender name/label
            if msg.from_person_id == PersonID("system"):
                sender_label = "system"
            elif msg.from_person_id == person.id:
                sender_label = person.name
            else:
                sender_label = str(msg.from_person_id)
                if hasattr(self._orchestrator, 'get_all_persons'):
                    persons = self._orchestrator.get_all_persons()
                    from_person_id = PersonID(str(msg.from_person_id))
                    if from_person_id in persons:
                        sender_label = persons[from_person_id].name or str(msg.from_person_id)
            
            # Include score in debug output for transparency
            lines.append(f"- {msg.id} ({sender_label}, score:{score:.1f}): {snippet}")
        
        listing = "\n".join(lines)
        print(f"\nSelecting memory: {len(unique_messages)} unique messages from {len(candidate_messages)} total, showing top {len(lines)}:\n")
        # Build prompt with at_most constraint if specified
        constraint_text = ""
        if at_most and at_most > 0:
            constraint_text = f"\nCONSTRAINT: Select at most {at_most} messages that best match the criteria.\n"
        
        prompt = (
            "CANDIDATE MESSAGES (id (sender): snippet):\n"
            f"{listing}\n\n===\n\n"
            f"TASK PREVIEW:\n===\n\n{preview}\n\n===\n\n"
            f"CRITERIA:\n{crit}\n\n"
            f"{constraint_text}"
            "IMPORTANT: Exclude messages that duplicate content already in the task preview.\n"
            "Return a JSON array of message IDs only."
        )

        # Execute via orchestrator so we keep the person-based architecture
        # Pass empty messages list since selector gets all info in the prompt
        result = await self._orchestrator.execute_person_completion(
            person=facet,
            prompt=prompt,
            llm_service=llm_service,
            execution_id="memory_selection",
            node_id="memory_selector",
            temperature=0.1,
            max_tokens=512,
            all_messages=[],  # Empty list - selector doesn't need conversation context
            # Note: record=False parameter would require orchestrator modification
            # For now, selector messages will be recorded but won't show in base person's view
        )

        # Robust parse
        text = getattr(result, "text", "") or ""
        try:
            data = json.loads(text)
        except Exception:
            m = re.search(r"\[.*?\]", text, re.S)
            data = json.loads(m.group(0)) if m else []
        ids = [str(x) for x in data if x]
        # Apply at_most trimming here or let caller do it; caller already does it after mapping
        return ids
    
    async def apply_memory_settings(
        self,
        *,
        person: Person,
        all_messages: Sequence[Message],
        memorize_to: Optional[str],
        at_most: Optional[int],
        task_prompt_preview: str = "",
        llm_service=None,
    ) -> list[Message]:
        """Apply memory settings to filter messages based on memorize_to configuration.
        
        Two modes of operation:
        1. Special keyword: GOLDFISH (no memory)
        2. LLM-based selection: Any other string triggers intelligent selection
           (empty/None uses default ALL_INVOLVED behavior)
        
        Args:
            person: The person for which we're filtering memory
            all_messages: All available messages
            memorize_to: Memory configuration string
            at_most: Maximum number of messages to keep
            task_prompt_preview: Preview of the task for LLM selection
            llm_service: LLM service for intelligent selection
            
        Returns:
            Filtered list of messages
        """
        if not memorize_to or not memorize_to.strip():
            # Default behavior: use ALL_INVOLVED filter internally
            return all_messages
        
        memorize_str = memorize_to.strip().upper()
        
        # Special case: GOLDFISH mode - no memory at all
        if memorize_str == "GOLDFISH":
            return []
        
        # Otherwise, use LLM-based intelligent selection
        if llm_service:
            # Use LLM to select relevant messages
            selected_ids = await self.select(
                person=person,
                candidate_messages=all_messages,
                task_prompt_preview=task_prompt_preview,
                criteria=memorize_to,  # Use the original string as criteria
                at_most=at_most,
                llm_service=llm_service,
            )
            
            # Map IDs back to messages
            id_to_msg = {str(msg.id): msg for msg in all_messages if hasattr(msg, "id")}
            selected_messages = [id_to_msg[id] for id in selected_ids if id in id_to_msg]
            
            # Apply limit if needed
            if at_most and len(selected_messages) > at_most:
                selected_messages = selected_messages[-at_most:]
            
            return selected_messages
        else:
            # Fallback to ALL_INVOLVED if no LLM service available
            return all_messages