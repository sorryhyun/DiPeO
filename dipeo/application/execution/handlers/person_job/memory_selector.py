import json
import re
from typing import Sequence, Optional

from dipeo.diagram_generated.domain_models import Message


class MemorySelector:
    def __init__(self, llm_service):
        self.llm = llm_service

    async def select(
        self,
        *,
        candidate_messages: Sequence[Message],
        task_prompt_preview: str,
        criteria: str,  # String only, comma-separated
        at_most: Optional[int],
    ) -> list[str]:
        """Return a list of message IDs (strings) to keep.
        
        Args:
            candidate_messages: Messages to select from
            task_prompt_preview: Preview of the task prompt for context
            criteria: Comma-separated string of selection criteria
            at_most: Maximum number of messages to select
        """
        if not criteria or not criteria.strip():
            return []
        
        # Parse comma-separated criteria
        criteria_list = [s.strip() for s in criteria.split(",") if s.strip()]
        if not criteria_list:
            return []
        
        # Build a compact, ID-driven listing to keep tokens low
        # (truncate content per message to ~300-500 chars to fit large histories)
        lines = []
        for m in candidate_messages:
            content = (m.content or "")[:500]
            role = "system" if str(m.from_person_id) == "system" else (
                   "assistant" if m.from_person_id == m.to_person_id else "user")
            lines.append(f"- id:{m.id or ''} role:{role} text:{json.dumps(content)}")

        sys_msg = (
          "You are a memory selector. Given a task and a list of prior messages, "
          "return a JSON array of up to N message IDs that would help the task. "
          "Prefer messages with instructions, requirements, references, and directly "
          "relevant prior analysis. Always keep crucial system-level instructions if present."
        )
        user_msg = (
          f"Task (preview): {task_prompt_preview[:1500]}\n"
          f"Criteria: {', '.join(criteria_list)}\n"
          f"At most: {at_most or 'no limit'}\n"
          "Messages:\n" + "\n".join(lines) + "\n\n"
          "Output strictly as JSON array of strings, e.g.: [\"msg123\", \"msg456\"]"
        )

        # Provider-agnostic call; the driver handles provider/model selection.
        result = await self.llm.complete(
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
            ], 
            response_format="json"  # driver accepts passthrough kwargs
        )

        # Robust parse: accept either JSON array or any text containing it
        try:
            data = json.loads(result.text)
            return [str(x) for x in data if x]
        except Exception:
            m = re.search(r"\[.*?\]", result.text, re.S)
            if not m:
                return []
            try:
                data = json.loads(m.group(0))
                return [str(x) for x in data if x]
            except Exception:
                return []