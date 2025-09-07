"""Token counting for LLM providers."""

import logging

from ..core.types import ProviderType, TokenUsage

logger = logging.getLogger(__name__)

# Approximate tokens per character for fallback estimation
TOKENS_PER_CHAR_ESTIMATE = {
    ProviderType.OPENAI: 0.25,  # ~4 chars per token
    ProviderType.ANTHROPIC: 0.25,  # Similar to OpenAI
    ProviderType.GOOGLE: 0.3,  # Slightly different tokenization
    ProviderType.OLLAMA: 0.25,  # Depends on model, using average
}

# Model-specific context limits
MODEL_CONTEXT_LIMITS = {
    # OpenAI models
    "gpt-5-nano-2025-08-07": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16384,
    "o3": 200000,  # O3 model
    "o3-mini": 200000,
    # Anthropic models
    "claude-3-5-sonnet": 200000,
    "claude-3-5-haiku": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-2.1": 200000,
    "claude-2": 100000,
    "claude-instant": 100000,
    # Google models
    "gemini-2.0-flash-exp": 1048576,
    "gemini-1.5-pro": 2097152,
    "gemini-1.5-flash": 1048576,
    "gemini-1.0-pro": 32768,
    # Ollama models (common ones)
    "llama3.3:70b": 8192,
    "llama3.3": 8192,
    "llama2": 4096,
    "mistral": 8192,
    "mixtral": 32768,
    "codellama": 16384,
}


class TokenCounter:
    """Counts tokens for different LLM providers."""

    def __init__(self, provider: ProviderType):
        """Initialize token counter for specific provider."""
        self.provider = provider
        self._tokenizer = None

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for specific model."""
        if self.provider == ProviderType.OPENAI:
            return self._count_openai_tokens(text, model)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._count_anthropic_tokens(text, model)
        elif self.provider == ProviderType.GOOGLE:
            return self._count_google_tokens(text, model)
        elif self.provider == ProviderType.OLLAMA:
            return self._count_ollama_tokens(text, model)
        else:
            return self._estimate_tokens(text)

    def _count_openai_tokens(self, text: str, model: str) -> int:
        """Count tokens for OpenAI models."""
        try:
            import tiktoken

            # Get the appropriate encoding for the model
            if (
                model.startswith("gpt-4")
                or model.startswith("gpt-5")
                or model.startswith("o3")
                or model.startswith("gpt-3.5")
            ):
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")  # Default

            tokens = encoding.encode(text)
            return len(tokens)

        except ImportError:
            logger.debug("tiktoken not available, using estimation")
            return self._estimate_tokens(text)
        except Exception as e:
            logger.warning(f"Error counting OpenAI tokens: {e}, using estimation")
            return self._estimate_tokens(text)

    def _count_anthropic_tokens(self, text: str, model: str) -> int:
        """Count tokens for Anthropic models."""
        try:
            # Anthropic uses a similar tokenization to OpenAI
            # For now, use estimation or tiktoken if available
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            # Anthropic tokenization is slightly different, apply adjustment
            return int(len(tokens) * 1.1)
        except ImportError:
            return self._estimate_tokens(text)

    def _count_google_tokens(self, text: str, model: str) -> int:
        """Count tokens for Google models."""
        # Google doesn't provide a public tokenizer
        # Use character-based estimation
        return self._estimate_tokens(text, provider_override=ProviderType.GOOGLE)

    def _count_ollama_tokens(self, text: str, model: str) -> int:
        """Count tokens for Ollama models."""
        # Token counting depends on the specific model
        # Use estimation based on model type
        if "llama" in model.lower():
            # Llama models use SentencePiece tokenization
            return int(len(text) * 0.3)  # Rough estimate
        else:
            return self._estimate_tokens(text)

    def _estimate_tokens(self, text: str, provider_override: ProviderType | None = None) -> int:
        """Estimate token count based on character count."""
        provider = provider_override or self.provider
        ratio = TOKENS_PER_CHAR_ESTIMATE.get(provider, 0.25)
        return int(len(text) * ratio)

    def count_messages_tokens(self, messages: list[dict[str, any]], model: str) -> int:
        """Count tokens in a list of messages."""
        total = 0

        for message in messages:
            # Count role tokens (usually 1-2 tokens)
            total += 4  # Overhead for message structure

            # Count content tokens
            content = message.get("content", "")
            if isinstance(content, str):
                total += self.count_tokens(content, model)
            elif isinstance(content, list):
                # Multimodal content
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            total += self.count_tokens(part.get("text", ""), model)
                        elif part.get("type") in ["image", "image_url"]:
                            # Images typically count as ~85 tokens for low res, ~765 for high res
                            total += 765  # Conservative estimate

            # Count name tokens if present
            if "name" in message:
                total += self.count_tokens(message["name"], model)

        return total

    def get_context_limit(self, model: str) -> int:
        """Get context limit for specific model."""
        # Check exact model match first
        if model in MODEL_CONTEXT_LIMITS:
            return MODEL_CONTEXT_LIMITS[model]

        # Check partial matches
        for model_key, limit in MODEL_CONTEXT_LIMITS.items():
            if model.startswith(model_key) or model_key in model:
                return limit

        # Default context limits by provider
        defaults = {
            ProviderType.OPENAI: 8192,
            ProviderType.ANTHROPIC: 100000,
            ProviderType.GOOGLE: 32768,
            ProviderType.OLLAMA: 4096,
        }

        return defaults.get(self.provider, 4096)

    def validate_token_limit(
        self, messages: list[dict[str, any]], model: str, max_tokens: int | None = None
    ) -> bool:
        """Validate if messages fit within model's context limit."""
        context_limit = self.get_context_limit(model)
        message_tokens = self.count_messages_tokens(messages, model)

        # Reserve tokens for output
        output_tokens = max_tokens or min(4096, context_limit // 4)

        total_required = message_tokens + output_tokens

        if total_required > context_limit:
            logger.warning(
                f"Token limit exceeded for {model}: "
                f"{total_required} > {context_limit} "
                f"(messages: {message_tokens}, output: {output_tokens})"
            )
            return False

        return True

    def create_usage(self, input_text: str, output_text: str, model: str) -> TokenUsage:
        """Create TokenUsage object from texts."""
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def truncate_to_limit(
        self, text: str, model: str, max_tokens: int, from_end: bool = False
    ) -> str:
        """Truncate text to fit within token limit."""
        current_tokens = self.count_tokens(text, model)

        if current_tokens <= max_tokens:
            return text

        # Binary search for the right truncation point
        if from_end:
            low, high = 0, len(text)
            while low < high:
                mid = (low + high) // 2
                truncated = text[-mid:]
                if self.count_tokens(truncated, model) <= max_tokens:
                    low = mid + 1
                else:
                    high = mid
            return text[-(low - 1) :]
        else:
            low, high = 0, len(text)
            while low < high:
                mid = (low + high + 1) // 2
                truncated = text[:mid]
                if self.count_tokens(truncated, model) <= max_tokens:
                    low = mid
                else:
                    high = mid - 1
            return text[:low]
