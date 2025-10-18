"""Response parsing utilities for Claude Code provider.

This module handles all response parsing logic for the Claude Code adapter,
including tool result extraction, phase-specific parsing, and structured output creation.
"""

import json
import logging
import re
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import ExecutionPhase
from dipeo.infrastructure.llm.drivers.types import LLMResponse, LLMUsage

logger = get_module_logger(__name__)


class ClaudeCodeResponseParser:
    """Parser for Claude Code responses with phase-specific handling."""

    @staticmethod
    async def collect_response(response_iterator) -> tuple[str, dict | None]:
        """Collect response text and tool invocation data from iterator."""
        result_text = ""
        tool_invocation_data = None

        async for message in response_iterator:
            # Check for tool invocations in AssistantMessage
            if hasattr(message, "content") and not hasattr(message, "result"):
                for block in message.content:
                    # Skip thinking blocks - only process tool_use blocks
                    block_type = getattr(block, "type", None)
                    if block_type == "thinking":
                        continue
                    if hasattr(block, "name") and hasattr(block, "input"):
                        if block.name.startswith("mcp__dipeo_structured_output__"):
                            tool_invocation_data = block.input
                            break

            # Process ResultMessage (final message, iterator auto-terminates after this)
            if hasattr(message, "result"):
                result_text = str(message.result)

        return result_text, tool_invocation_data

    @staticmethod
    def extract_usage_from_response(response_text: str) -> LLMUsage | None:
        """Extract token usage from response metadata if present."""
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
    def extract_tool_result(response_text: str) -> dict | None:
        """Extract tool result data from response text."""
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                if "data" in data:
                    return data["data"]
                if "message_ids" in data or "decision" in data:
                    return data
        except (json.JSONDecodeError, ValueError) as e:
            pass

        # Fallback: Look for JSON objects in the text
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.finditer(json_pattern, response_text)
        for match in matches:
            try:
                data = json.loads(match.group(0))
                if "message_ids" in data or "decision" in data:
                    return data
            except (json.JSONDecodeError, ValueError):
                continue

        return None

    @staticmethod
    def parse_memory_selection(response: str) -> Any:
        """Parse memory selection response into MemorySelectionOutput."""
        from dipeo.infrastructure.llm.drivers.types import MemorySelectionOutput

        message_ids = []

        json_pattern = r"\[[\s\S]*?\]"
        matches = re.findall(json_pattern, response)
        for match in matches:
            try:
                potential_ids = json.loads(match)
                if isinstance(potential_ids, list):
                    message_ids = [str(id) for id in potential_ids if id]
                    break
            except (json.JSONDecodeError, ValueError):
                continue

        # If no JSON found, look for comma-separated IDs
        if not message_ids:
            id_pattern = r"\b[a-zA-Z0-9_-]{6,}\b"
            potential_ids = re.findall(id_pattern, response)
            if potential_ids:
                message_ids = potential_ids[:20]

        return MemorySelectionOutput(message_ids=message_ids)

    @staticmethod
    def parse_decision(response: str) -> Any:
        """Parse decision response (YES/NO) into DecisionOutput."""
        from dipeo.infrastructure.llm.drivers.types import DecisionOutput

        clean_response = response.strip().upper()

        if any(keyword in clean_response for keyword in ["YES", "TRUE", "CORRECT", "AFFIRMATIVE"]):
            decision = True
        elif any(keyword in clean_response for keyword in ["NO", "FALSE", "INCORRECT", "NEGATIVE"]):
            decision = False
        else:
            logger.warning(
                f"[ClaudeCode] Unclear decision response: {response[:100]}, defaulting to False"
            )
            decision = False

        return DecisionOutput(decision=decision)

    @staticmethod
    def parse_response_with_tool_data(
        tool_data: dict, execution_phase: ExecutionPhase | None = None
    ) -> LLMResponse:
        """Parse tool invocation data to LLMResponse with structured output."""
        structured_output = None

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            from dipeo.infrastructure.llm.drivers.types import MemorySelectionOutput

            message_ids = tool_data.get("message_ids", [])
            structured_output = MemorySelectionOutput(message_ids=message_ids)

        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            from dipeo.infrastructure.llm.drivers.types import DecisionOutput

            decision = tool_data.get("decision", False)
            structured_output = DecisionOutput(decision=decision)

        from dipeo.infrastructure.llm.drivers.types import ProviderType

        return LLMResponse(
            content=str(structured_output) if structured_output else str(tool_data),
            model="claude-code",
            provider=ProviderType.CLAUDE_CODE,
            structured_output=structured_output,
            usage=None,
        )

    @staticmethod
    def parse_response(response: str, execution_phase: ExecutionPhase | None = None) -> LLMResponse:
        """Parse Claude Code response to LLMResponse with optional structured output."""
        usage = ClaudeCodeResponseParser.extract_usage_from_response(response)

        clean_response = re.sub(
            r"Tokens:\s*input=\d+,\s*output=\d+,\s*total=\d+", "", response
        ).strip()

        structured_output = None
        tool_result = ClaudeCodeResponseParser.extract_tool_result(response)

        if tool_result:
            if execution_phase == ExecutionPhase.MEMORY_SELECTION:
                from dipeo.infrastructure.llm.drivers.types import MemorySelectionOutput

                structured_output = MemorySelectionOutput(
                    message_ids=tool_result.get("message_ids", [])
                )
            elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
                from dipeo.infrastructure.llm.drivers.types import DecisionOutput

                structured_output = DecisionOutput(decision=tool_result.get("decision", False))
        else:
            # Fallback to text parsing if no tool result
            if execution_phase == ExecutionPhase.MEMORY_SELECTION:
                structured_output = ClaudeCodeResponseParser.parse_memory_selection(clean_response)
            elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
                structured_output = ClaudeCodeResponseParser.parse_decision(clean_response)

        from dipeo.infrastructure.llm.drivers.types import ProviderType

        return LLMResponse(
            content=clean_response,
            model="claude-code",
            provider=ProviderType.CLAUDE_CODE,
            structured_output=structured_output,
            usage=usage,
        )
