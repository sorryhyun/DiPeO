"""LLM Domain Service - Core business logic for LLM operations."""

from typing import Any

from dipeo.diagram_generated import LLMService
from ..value_objects import ModelConfig, RetryStrategy, RetryType, TokenLimits


class LLMDomainService:
    """Domain service for LLM-related business logic."""
    
    # Model-specific token limits
    _TOKEN_LIMITS = {
        # OpenAI models
        "gpt-4.1-nano": TokenLimits(context_window=4096, max_output_tokens=4096),
        "gpt-4": TokenLimits(context_window=8192, max_output_tokens=4096),
        "gpt-4-32k": TokenLimits(context_window=32768, max_output_tokens=16384),
        "gpt-4-turbo": TokenLimits(context_window=128000, max_output_tokens=4096),
        "gpt-4o": TokenLimits(context_window=128000, max_output_tokens=4096),
        "gpt-4o-mini": TokenLimits(context_window=128000, max_output_tokens=16384),
        "gpt-3.5-turbo": TokenLimits(context_window=16385, max_output_tokens=4096),
        "gpt-3.5-turbo-16k": TokenLimits(context_window=16385, max_output_tokens=4096),
        
        # Anthropic models
        "claude-3-opus": TokenLimits(context_window=200000, max_output_tokens=4096),
        "claude-3-sonnet": TokenLimits(context_window=200000, max_output_tokens=4096),
        "claude-3-haiku": TokenLimits(context_window=200000, max_output_tokens=4096),
        "claude-2.1": TokenLimits(context_window=200000, max_output_tokens=4096),
        "claude-2": TokenLimits(context_window=100000, max_output_tokens=4096),
        "claude-instant-1.2": TokenLimits(context_window=100000, max_output_tokens=4096),
        
        # Google models
        "gemini-pro": TokenLimits(context_window=32760, max_output_tokens=8192),
        "gemini-pro-vision": TokenLimits(context_window=16384, max_output_tokens=2048),
        "gemini-1.5-pro": TokenLimits(context_window=1048576, max_output_tokens=8192),
        "gemini-1.5-flash": TokenLimits(context_window=1048576, max_output_tokens=8192),
        "gemini-2.0-flash": TokenLimits(context_window=1048576, max_output_tokens=8192),
        "gemini-2.0-flash-exp": TokenLimits(context_window=1048576, max_output_tokens=8192),
        "gemini-2.5-pro": TokenLimits(context_window=2097152, max_output_tokens=8192),  # 2M context
        "gemini-2.5-flash": TokenLimits(context_window=1048576, max_output_tokens=8192),
        "gemini-2.5-flash-lite": TokenLimits(context_window=1048576, max_output_tokens=8192),
    }
    
    # Provider-specific validation rules
    _PROVIDER_RULES = {
        LLMService.OPENAI.value: {
            "allowed_params": ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty", "stop", "tools"],
            "temperature_range": (0, 2),
            "requires_api_key": True,
        },
        LLMService.ANTHROPIC.value: {
            "allowed_params": ["temperature", "max_tokens", "top_p", "top_k", "stop_sequences"],
            "temperature_range": (0, 1),
            "requires_api_key": True,
        },
        LLMService.GOOGLE.value: {
            "allowed_params": ["temperature", "max_tokens", "top_p", "top_k", "stop_sequences"],
            "temperature_range": (0, 1),
            "requires_api_key": True,
        },
        LLMService.OLLAMA.value: {
            "allowed_params": ["temperature", "max_tokens", "top_p", "top_k", "seed", "num_predict"],
            "temperature_range": (0, 2),
            "requires_api_key": False,  # Ollama doesn't require API keys
        },
    }
    
    def validate_model_config(self, provider: str, model: str, config: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate model configuration against provider rules.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if provider is supported
        provider_lower = provider.lower()
        if provider_lower not in self._PROVIDER_RULES:
            return False, f"Unsupported provider: {provider}"
        
        rules = self._PROVIDER_RULES[provider_lower]
        
        # Check allowed parameters
        allowed_params = set(rules["allowed_params"])
        for param in config:
            if param not in allowed_params:
                return False, f"Parameter '{param}' not allowed for provider {provider}"
        
        # Validate temperature if present
        if "temperature" in config:
            temp_min, temp_max = rules["temperature_range"]
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or not temp_min <= temp <= temp_max:
                return False, f"Temperature must be between {temp_min} and {temp_max}"
        
        # Validate max_tokens if present
        if "max_tokens" in config:
            max_tokens = config["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                return False, "max_tokens must be a positive integer"
        
        return True, None
    
    def calculate_token_limits(self, provider: str, model: str) -> TokenLimits | None:
        """
        Calculate token limits for a given provider and model.
        
        Returns:
            TokenLimits object or None if model not found
        """
        # Try exact match first
        if model in self._TOKEN_LIMITS:
            return self._TOKEN_LIMITS[model]
        
        # Try provider-specific defaults
        if provider.lower() == LLMService.OPENAI.value and model.startswith("gpt-"):
            # Default for unknown GPT models
            return TokenLimits(context_window=8192, max_output_tokens=4096)
        elif provider.lower() == LLMService.ANTHROPIC.value and model.startswith("claude-"):
            # Default for unknown Claude models
            return TokenLimits(context_window=100000, max_output_tokens=4096)
        elif provider.lower() == LLMService.GOOGLE.value and model.startswith("gemini-"):
            # Default for unknown Gemini models
            return TokenLimits(context_window=32760, max_output_tokens=8192)
        
        return None
    
    def determine_retry_strategy(self, error: Exception) -> RetryStrategy:
        """
        Determine retry strategy based on error type.
        
        Returns:
            Appropriate RetryStrategy for the error
        """
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Rate limit errors - use exponential backoff
        if "rate" in error_message and "limit" in error_message:
            return RetryStrategy(
                retry_type=RetryType.EXPONENTIAL_BACKOFF,
                max_retries=5,
                initial_delay_seconds=2.0,
                max_delay_seconds=120.0,
                backoff_factor=2.0
            )
        
        # Timeout errors - use linear backoff
        if "timeout" in error_message:
            return RetryStrategy(
                retry_type=RetryType.LINEAR_BACKOFF,
                max_retries=3,
                initial_delay_seconds=1.0,
                max_delay_seconds=10.0,
                backoff_factor=1.0
            )
        
        # API errors (5xx) - use exponential backoff
        if any(code in error_message for code in ["500", "502", "503", "504"]):
            return RetryStrategy(
                retry_type=RetryType.EXPONENTIAL_BACKOFF,
                max_retries=3,
                initial_delay_seconds=1.0,
                max_delay_seconds=30.0,
                backoff_factor=2.0
            )
        
        # Authentication errors - no retry
        if any(word in error_message for word in ["auth", "api key", "unauthorized", "403"]):
            return RetryStrategy.no_retry()
        
        # Invalid request errors - no retry
        if any(word in error_message for word in ["invalid", "bad request", "400"]):
            return RetryStrategy.no_retry()
        
        # Default strategy for unknown errors
        return RetryStrategy.default()
    
    def estimate_tokens(self, text: str, provider: str) -> int:
        """
        Estimate token count for text based on provider.
        
        This is a simplified estimation. In production, use proper tokenizers.
        """
        # Rough estimation: ~4 characters per token for English
        # Different providers may count differently
        if provider.lower() == LLMService.OPENAI.value or provider.lower() == LLMService.ANTHROPIC.value:
            return len(text) // 4
        elif provider.lower() == LLMService.GOOGLE.value:
            return len(text) // 3  # Google tends to count more tokens
        else:
            return len(text) // 4  # Default estimation
    
    def validate_prompt_size(self, prompt: str, provider: str, model: str) -> tuple[bool, str | None]:
        """
        Validate if prompt fits within model's context window.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        token_limits = self.calculate_token_limits(provider, model)
        if not token_limits:
            return True, None  # Can't validate without limits
        
        estimated_tokens = self.estimate_tokens(prompt, provider)
        
        # Leave room for response (use half context window as safe limit)
        safe_limit = token_limits.context_window // 2
        
        if estimated_tokens > safe_limit:
            return False, f"Prompt too long: ~{estimated_tokens} tokens (safe limit: {safe_limit})"
        
        return True, None
    
    def create_model_config(
        self,
        provider: str,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs
    ) -> ModelConfig:
        """Create a validated ModelConfig instance."""
        # Apply provider-specific defaults
        if temperature is None:
            temperature = 0.7
        
        # Get token limits to set sensible max_tokens default
        if max_tokens is None:
            token_limits = self.calculate_token_limits(provider, model)
            if token_limits:
                max_tokens = min(4096, token_limits.max_output_tokens)
        
        return ModelConfig(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=kwargs.get("top_p", 1.0),
            frequency_penalty=kwargs.get("frequency_penalty", 0.0),
            presence_penalty=kwargs.get("presence_penalty", 0.0)
        )