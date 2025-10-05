"""Response conversion utilities for LLM services."""

from dipeo.diagram_generated import ChatResult
from dipeo.domain.base.mixins import LoggingMixin
from dipeo.infrastructure.llm.drivers.types import LLMResponse


class ResponseConverter(LoggingMixin):
    """Converts LLM responses to ChatResult format."""

    def convert_to_chat_result(self, response: LLMResponse) -> ChatResult:
        """Convert LLMResponse to ChatResult."""
        # Check for structured output first (from responses.parse())
        if response.structured_output is not None:
            if hasattr(response.structured_output, "model_dump_json"):
                content = response.structured_output.model_dump_json()
            elif hasattr(response.structured_output, "dict"):
                import json

                content = json.dumps(response.structured_output.dict())
                self.log_debug(f"Structured output converted via dict: {content[:200]}")
            else:
                content = str(response.structured_output)
                self.log_debug(f"Structured output converted via str: {content[:200]}")
        elif isinstance(response.content, str):
            content = response.content
        elif hasattr(response.content, "model_dump_json"):
            content = response.content.model_dump_json()
        elif hasattr(response.content, "dict"):
            import json

            content = json.dumps(response.content.dict())
        else:
            content = str(response.content)

        result = ChatResult(text=content)

        if response.usage:
            result.llm_usage = response.usage

        return result
