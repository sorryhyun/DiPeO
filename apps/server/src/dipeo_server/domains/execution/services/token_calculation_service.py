
import logging
from typing import Dict, Optional

from dipeo_domain import NodeOutput, TokenUsage

logger = logging.getLogger(__name__)


class TokenCalculationService:
    """Service responsible for token usage calculations and aggregations."""

    @staticmethod
    def aggregate_node_token_usage(
        node_outputs: Dict[str, NodeOutput],
    ) -> Optional[TokenUsage]:
        total_token_usage = None

        for node_id, output in node_outputs.items():
            if not output or not output.metadata:
                continue

            # Extract token usage from node metadata
            token_usage_data = output.metadata.get("tokenUsage")
            if not token_usage_data or not isinstance(token_usage_data, dict):
                continue

            # Create TokenUsage object from the data
            node_tokens = TokenUsage(
                input=token_usage_data.get("input", 0),
                output=token_usage_data.get("output", 0),
                cached=token_usage_data.get("cached", 0),
                total=token_usage_data.get("total", 0),
            )

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
                total_token_usage = TokenCalculationService._add_token_usage(
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
    def _add_token_usage(usage1: TokenUsage, usage2: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input=usage1.input + usage2.input,
            output=usage1.output + usage2.output,
            cached=(usage1.cached or 0) + (usage2.cached or 0),
            total=(usage1.total or 0) + (usage2.total or 0),
        )

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
