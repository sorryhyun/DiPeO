import logging
from typing import Any, Dict, Optional

from dipeo_domain import NodeOutput, TokenUsage

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
    def to_dict(usage: TokenUsage) -> Dict[str, float]:
        return {
            "input": usage.input,
            "output": usage.output,
            "cached": usage.cached or 0,
            "total": usage.total or (usage.input + usage.output),
        }

    @staticmethod
    def from_response(response: dict) -> TokenUsage:
        return TokenUsage(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0),
        )

    @staticmethod
    def from_usage(usage: Any, service: Optional[str] = None) -> TokenUsage:
        if not usage:
            return TokenUsageService.zero()

        if service == "gemini" and isinstance(usage, (list, tuple)):
            return TokenUsage(
                input=usage[0] if len(usage) > 0 else 0,
                output=usage[1] if len(usage) > 1 else 0,
            )

        if service == "openai":
            return TokenUsage(
                input=usage["prompt_tokens"],
                output=usage["completion_tokens"],
                total=usage["prompt_tokens"] + usage["completion_tokens"],
            )

        input_tokens = (
            getattr(usage, "input_tokens", None)
            or getattr(usage, "prompt_tokens", None)
            or 0
        )
        output_tokens = (
            getattr(usage, "output_tokens", None)
            or getattr(usage, "completion_tokens", None)
            or 0
        )
        cached_tokens = 0

        return TokenUsage(
            input=input_tokens, output=output_tokens, cached=cached_tokens
        )

    @staticmethod
    def aggregate_node_token_usage(
        node_outputs: Dict[str, NodeOutput],
    ) -> Optional[TokenUsage]:
        total_token_usage = None

        for node_id, output in node_outputs.items():
            if not output or not output.metadata:
                continue

            # Extract token usage from node metadata
            node_tokens = TokenUsageService.extract_token_usage_from_metadata(
                output.metadata
            )
            if not node_tokens:
                continue

            # Calculate total if not provided
            if not node_tokens.total:
                node_tokens.total = node_tokens.input + node_tokens.output

            logger.debug(
                f"Node {node_id} token usage: input={node_tokens.input}, "
                f"output={node_tokens.output}, total={node_tokens.total}"
            )

            # Aggregate with existing total
            if total_token_usage is None:
                total_token_usage = node_tokens
            else:
                total_token_usage = TokenUsageService.add(
                    total_token_usage, node_tokens
                )

        if total_token_usage:
            # Ensure total is properly calculated
            if not total_token_usage.total or total_token_usage.total == 0:
                total_token_usage.total = (
                    total_token_usage.input + total_token_usage.output
                )

            logger.info(
                f"Total token usage: input={total_token_usage.input}, "
                f"output={total_token_usage.output}, total={total_token_usage.total}"
            )

        return total_token_usage

    @staticmethod
    def extract_token_usage_from_metadata(metadata: Dict) -> Optional[TokenUsage]:
        token_usage_data = metadata.get("tokenUsage")
        if not token_usage_data or not isinstance(token_usage_data, dict):
            return None

        return TokenUsage(
            input=token_usage_data.get("input", 0),
            output=token_usage_data.get("output", 0),
            cached=token_usage_data.get("cached", 0),
            total=token_usage_data.get("total", 0),
        )

    @staticmethod
    def extract_from_personjob_output(value: Any) -> Optional[TokenUsage]:
        """Extract token usage from PersonJob output."""
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            return TokenUsage(
                input=int(value.get("input_tokens", 0)),
                output=int(value.get("output_tokens", 0)),
                cached=int(value.get("cached_tokens", 0)),
            )
        return None

    @staticmethod
    def to_personjob_metadata(token_usage: Optional[TokenUsage]) -> Dict[str, str]:
        """Convert TokenUsage to PersonJob metadata format."""
        metadata = {}
        if token_usage:
            if token_usage.total and token_usage.total > 0:
                metadata["token_count"] = str(token_usage.total)
            elif token_usage.input + token_usage.output > 0:
                metadata["token_count"] = str(token_usage.input + token_usage.output)

            if token_usage.input > 0:
                metadata["input_tokens"] = str(token_usage.input)
            if token_usage.output > 0:
                metadata["output_tokens"] = str(token_usage.output)
            if token_usage.cached and token_usage.cached > 0:
                metadata["cached_tokens"] = str(token_usage.cached)
        return metadata
