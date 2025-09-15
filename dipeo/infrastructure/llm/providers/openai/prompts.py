MEMORY_SELECTION_PROMPT = """
    You are in MEMORY SELECTION MODE.
    - Input: a candidate list of prior messages with their IDs,
    "the upcoming task preview, and a natural-language selection criteria.
    - Output: Return a structured response with a 'message_ids' field containing an array of message IDs to keep.\n"
    - IMPORTANT: Do NOT select messages whose content is already included in or duplicated by "
    the task preview. Avoid redundancy.\n"
    - When a CONSTRAINT specifies maximum messages, respect it strictly and select "
    the MOST relevant messages within that limit.\n"
    - Favor precision over recall; choose the smallest set that satisfies the criteria.\n"
    - If uncertain, return an empty array."""

LLM_DECISION_PROMPT = """
    You are in DECISION MODE.
    - Evaluate the provided context and make a binary decision.
    - Return a structured response with a 'decision' field:
      - decision: true for YES/affirmative/valid/approved
      - decision: false for NO/negative/invalid/rejected
    - Be decisive and clear in your judgment."""
