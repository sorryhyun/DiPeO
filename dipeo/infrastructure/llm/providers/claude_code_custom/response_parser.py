"""Response parsing for Claude Code Custom provider."""

import json
import re

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.infrastructure.llm.drivers.types import ExecutionPhase, LLMResponse

logger = get_module_logger(__name__)


class ResponseParser:
    """Parse responses from Claude Code SDK for different execution phases."""

    @staticmethod
    def extract_usage_from_response(response_text: str) -> LLMUsage | None:
        """Extract token usage from response if included."""
        usage_pattern = r"Tokens:\s*input=(\d+),\s*output=(\d+),\s*total=(\d+)"
        match = re.search(usage_pattern, response_text)

        if match:
            return LLMUsage(
                input_tokens=int(match.group(1)),
                output_tokens=int(match.group(2)),
                total_tokens=int(match.group(3)),
            )
        return None

    @staticmethod
    def parse_response(response: str, execution_phase: ExecutionPhase | None = None) -> LLMResponse:
        """Parse response from Claude Code SDK."""
        usage = ResponseParser.extract_usage_from_response(response)

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            json_pattern = r"\[[\d,\s]+\]"
            match = re.search(json_pattern, response)
            if match:
                try:
                    selected_ids = json.loads(match.group())
                    return LLMResponse(
                        content=str(selected_ids), selected_ids=selected_ids, usage=usage
                    )
                except json.JSONDecodeError:
                    pass

            numbers = re.findall(r"\b\d+\b", response)
            if numbers:
                selected_ids = [int(n) for n in numbers]
                return LLMResponse(content=response, selected_ids=selected_ids, usage=usage)

        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            response_lower = response.lower()
            if any(word in response_lower for word in ["yes", "true", "correct", "affirmative"]):
                decision = True
            elif any(word in response_lower for word in ["no", "false", "incorrect", "negative"]):
                decision = False
            else:
                decision = False

            return LLMResponse(content=response, decision=decision, usage=usage)

        return LLMResponse(content=response, usage=usage)

    @staticmethod
    def parse_response_with_tool_data(
        tool_data: dict, execution_phase: ExecutionPhase | None = None
    ) -> LLMResponse:
        """Parse response when MCP tool was invoked (structured output)."""
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            selected_ids = tool_data.get("message_ids", [])
            return LLMResponse(content=str(selected_ids), selected_ids=selected_ids)
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            decision = tool_data.get("decision", False)
            return LLMResponse(content=str(decision), decision=decision)

        return LLMResponse(content=str(tool_data))
