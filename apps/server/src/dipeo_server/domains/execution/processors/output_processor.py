from typing import TYPE_CHECKING, Any, Optional

from dipeo_server.domains.llm.token_usage_service import TokenUsageService

if TYPE_CHECKING:
    from dipeo_domain import TokenUsage


class OutputProcessor:
    """Processor for handling PersonJob and other wrapped outputs."""

    @staticmethod
    def extract_value(value: Any) -> Any:
        """Extract actual value from wrapped outputs."""
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            return value.get("text", "")
        return value

    @staticmethod
    def extract_conversation_history(value: Any) -> list[dict[str, str]]:
        """Extract conversation history from PersonJob output."""
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            return value.get("conversation_history", [])
        return []

    @staticmethod
    def extract_metadata(value: Any) -> dict[str, Any]:
        """Extract metadata from PersonJob output."""
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            metadata = {}
            if "token_count" in value:
                metadata["token_count"] = value["token_count"]
            if "input_tokens" in value:
                metadata["input_tokens"] = value["input_tokens"]
            if "output_tokens" in value:
                metadata["output_tokens"] = value["output_tokens"]
            if "cached_tokens" in value:
                metadata["cached_tokens"] = value["cached_tokens"]
            if "model" in value:
                metadata["model"] = value["model"]
            if "execution_time" in value:
                metadata["execution_time"] = value["execution_time"]
            return metadata
        return {}

    @staticmethod
    def is_personjob_output(value: Any) -> bool:
        return isinstance(value, dict) and value.get("_type") == "personjob_output"

    @staticmethod
    def process_list(values: list[Any]) -> list[Any]:
        return [OutputProcessor.extract_value(v) for v in values]

    @staticmethod
    def create_personjob_output(
        text: str,
        conversation_history: list[dict[str, str]] | None = None,
        token_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        model: str | None = None,
    ) -> dict[str, Any]:
        output = {"_type": "personjob_output", "text": text}

        if conversation_history is not None:
            output["conversation_history"] = conversation_history

        # Create TokenUsage object and use TokenUsageService for conversion
        if any([token_count, input_tokens, output_tokens, cached_tokens]):
            from dipeo_domain import TokenUsage

            # Use token_count as total, or calculate from input+output
            total = token_count if token_count > 0 else (input_tokens + output_tokens)

            token_usage = TokenUsage(
                input=input_tokens,
                output=output_tokens,
                cached=cached_tokens,
                total=total,
            )
            token_metadata = TokenUsageService.to_personjob_metadata(token_usage)
            output.update(token_metadata)

        if model:
            output["model"] = model

        return output

    @staticmethod
    def create_personjob_output_from_tokens(
        text: str,
        token_usage: "TokenUsage",
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
        execution_time: float | None = None,
    ) -> dict[str, Any]:
        output = {"_type": "personjob_output", "text": text}

        if conversation_history is not None:
            output["conversation_history"] = conversation_history

        # Use TokenUsageService to convert token usage to metadata format
        token_metadata = TokenUsageService.to_personjob_metadata(token_usage)
        output.update(token_metadata)

        if model:
            output["model"] = model
        if execution_time is not None:
            output["execution_time"] = str(execution_time)

        return output

    @staticmethod
    def extract_token_usage(value: Any) -> Optional["TokenUsage"]:
        """Extract token usage from PersonJob output using TokenUsageService."""
        return TokenUsageService.extract_from_personjob_output(value)
