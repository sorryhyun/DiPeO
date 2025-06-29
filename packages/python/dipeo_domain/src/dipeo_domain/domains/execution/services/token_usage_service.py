"""Token usage service for the domain layer."""

import logging
from typing import Any

from dipeo_domain.models import NodeOutput, TokenUsage

logger = logging.getLogger(__name__)


class TokenUsageService:
    @staticmethod
    def zero() -> TokenUsage:
        return TokenUsage(input=0, output=0, cached=0)

    @staticmethod
    def add(first: TokenUsage, second: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input=first.input + second.input,
            output=first.output + second.output,
            cached=(first.cached or 0) + (second.cached or 0),
        )

    @staticmethod
    def to_dict(usage: TokenUsage) -> dict[str, float]:
        return {
            "input": usage.input,
            "output": usage.output,
            "cached": usage.cached or 0,
            "total": usage.total or (usage.input + usage.output),
        }

    @staticmethod
    def from_chat_result(
        prompt_tokens: int, completion_tokens: int, total_tokens: int | None = None
    ) -> TokenUsage:
        """Create TokenUsage from standardized ChatResult format."""
        return TokenUsage(
            input=prompt_tokens,
            output=completion_tokens,
            total=total_tokens or (prompt_tokens + completion_tokens),
        )

    @staticmethod
    def aggregate_node_outputs(outputs: dict[str, NodeOutput]) -> TokenUsage:
        total = TokenUsageService.zero()
        for output in outputs.values():
            if output.tokenUsage:
                total = TokenUsageService.add(total, output.tokenUsage)
        return total

    @staticmethod
    def to_personjob_metadata(token_usage: TokenUsage | None) -> dict[str, Any]:
        if not token_usage:
            return {}

        metadata = {
            "input_tokens": token_usage.input,
            "output_tokens": token_usage.output,
            "token_count": token_usage.input + token_usage.output,
        }

        if token_usage.cached:
            metadata["cached_tokens"] = token_usage.cached

        return metadata

    @staticmethod
    def extract_from_personjob_output(value: Any) -> TokenUsage | None:
        """Extract token usage from PersonJob output."""
        if not isinstance(value, dict) or value.get("_type") != "personjob_output":
            return None

        if "input_tokens" in value and "output_tokens" in value:
            return TokenUsage(
                input=value.get("input_tokens", 0),
                output=value.get("output_tokens", 0),
                cached=value.get("cached_tokens", 0),
            )

        return None
