from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    def extract_conversation_history(value: Any) -> List[Dict[str, str]]:
        """Extract conversation history from PersonJob output."""
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            return value.get("conversation_history", [])
        return []

    @staticmethod
    def extract_metadata(value: Any) -> Dict[str, Any]:
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
    def process_list(values: List[Any]) -> List[Any]:
        return [OutputProcessor.extract_value(v) for v in values]

    @staticmethod
    def create_personjob_output(
        text: str,
        conversation_history: List[Dict[str, str]] = None,
        token_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        model: str = None,
    ) -> Dict[str, Any]:
        output = {"_type": "personjob_output", "text": text}

        if conversation_history is not None:
            output["conversation_history"] = conversation_history
        if token_count > 0:
            output["token_count"] = str(token_count)
        if input_tokens > 0:
            output["input_tokens"] = str(input_tokens)
        if output_tokens > 0:
            output["output_tokens"] = str(output_tokens)
        if cached_tokens > 0:
            output["cached_tokens"] = str(cached_tokens)
        if model:
            output["model"] = model

        return output

    @staticmethod
    def create_personjob_output_from_tokens(
        text: str,
        token_usage: "TokenUsage",
        conversation_history: List[Dict[str, str]] = None,
        model: str = None,
        execution_time: float = None,
    ) -> Dict[str, Any]:
        output = {"_type": "personjob_output", "text": text}

        if conversation_history is not None:
            output["conversation_history"] = conversation_history
        if token_usage:
            if token_usage.total > 0:
                output["token_count"] = str(token_usage.total)
            if token_usage.input > 0:
                output["input_tokens"] = str(token_usage.input)
            if token_usage.output > 0:
                output["output_tokens"] = str(token_usage.output)
            if token_usage.cached > 0:
                output["cached_tokens"] = str(token_usage.cached)
        if model:
            output["model"] = model
        if execution_time is not None:
            output["execution_time"] = str(execution_time)

        return output

    @staticmethod
    def extract_token_usage(value: Any) -> Optional["TokenUsage"]:
        if isinstance(value, dict) and value.get("_type") == "personjob_output":
            from dipeo_domain import TokenUsage

            return TokenUsage(
                input=int(value.get("input_tokens", 0)),
                output=int(value.get("output_tokens", 0)),
                cached=int(value.get("cached_tokens", 0)),
            )
        return None
