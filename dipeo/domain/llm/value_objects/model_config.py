"""Model configuration value object."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    """Value object representing LLM model configuration."""
    
    provider: str
    model: str
    temperature: float | None = 0.2
    max_tokens: int | None = None
    top_p: float | None = 1.0
    frequency_penalty: float | None = 0.0
    presence_penalty: float | None = 0.0
    
    def __post_init__(self):
        """Validate configuration values."""
        if not self.provider:
            raise ValueError("Provider cannot be empty")
        if not self.model:
            raise ValueError("Model cannot be empty")
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if self.top_p is not None and not 0 <= self.top_p <= 1:
            raise ValueError("Top-p must be between 0 and 1")
        if self.frequency_penalty is not None and not -2 <= self.frequency_penalty <= 2:
            raise ValueError("Frequency penalty must be between -2 and 2")
        if self.presence_penalty is not None and not -2 <= self.presence_penalty <= 2:
            raise ValueError("Presence penalty must be between -2 and 2")
    
    def to_api_params(self) -> dict[str, Any]:
        """Convert to API parameters."""
        params = {
            "model": self.model,
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p != 1.0:
            params["top_p"] = self.top_p
        if self.frequency_penalty != 0.0:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty != 0.0:
            params["presence_penalty"] = self.presence_penalty
        return params