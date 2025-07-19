"""Token limits value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenLimits:
    """Value object representing token limits for an LLM model."""
    
    context_window: int
    max_output_tokens: int
    tokens_per_message: int = 3  # OpenAI's per-message overhead
    tokens_per_name: int = 1  # Additional tokens when name is present
    
    def __post_init__(self):
        """Validate token limits."""
        if self.context_window <= 0:
            raise ValueError("Context window must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("Max output tokens must be positive")
        if self.max_output_tokens > self.context_window:
            raise ValueError("Max output tokens cannot exceed context window")
        if self.tokens_per_message < 0:
            raise ValueError("Tokens per message cannot be negative")
        if self.tokens_per_name < 0:
            raise ValueError("Tokens per name cannot be negative")
    
    def calculate_available_tokens(self, input_tokens: int) -> int:
        """Calculate available tokens for output given input tokens."""
        available = self.context_window - input_tokens
        return min(available, self.max_output_tokens)
    
    def is_within_limits(self, input_tokens: int, output_tokens: int) -> bool:
        """Check if token counts are within limits."""
        total = input_tokens + output_tokens
        return (
            total <= self.context_window and
            output_tokens <= self.max_output_tokens
        )