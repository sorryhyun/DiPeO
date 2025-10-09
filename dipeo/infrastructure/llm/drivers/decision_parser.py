"""Decision parsing utilities for LLM services."""

import json
import re

from dipeo.domain.base.mixins import LoggingMixin


class DecisionParser(LoggingMixin):
    """Parses binary decisions from text responses."""

    def parse_text_decision(self, response_text: str) -> bool:
        """Parse a binary decision from text response."""
        if not response_text:
            return False

        response_stripped = response_text.strip()

        # Try to parse as JSON first
        if response_stripped.startswith("{") and response_stripped.endswith("}"):
            try:
                json_data = json.loads(response_stripped)
                if "decision" in json_data:
                    return bool(json_data["decision"])
            except (json.JSONDecodeError, ValueError):
                pass

        # Clean and check for keywords
        response_lower = response_text.lower().strip()
        response_lower = re.sub(r"[*_`#\[\]()]", "", response_lower)

        # Check start of response
        if response_lower.startswith("yes"):
            return True
        if response_lower.startswith("no"):
            return False

        # Keyword matching (limited to 4 most essential keywords each)
        affirmative_keywords = ["yes", "true", "correct", "pass"]
        negative_keywords = ["no", "false", "incorrect", "fail"]

        affirmative_count = sum(1 for keyword in affirmative_keywords if keyword in response_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in response_lower)

        if affirmative_count > negative_count:
            return True
        elif negative_count > affirmative_count:
            return False

        self.log_warning(f"Ambiguous decision response: {response_text[:100]}...")
        return False
