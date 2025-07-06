"""LLM Service port interface."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMServicePort(Protocol):
    """Port for LLM service operations.
    
    This interface defines the contract for LLM adapters that integrate
    with various providers (OpenAI, Claude, Gemini, etc.).
    """

    async def complete(
        self,
        messages: List[Dict[str, str]],  # Standard format: [{"role": "user", "content": "..."}]
        model: str,
        api_key_id: str,
        **kwargs,  # Provider-specific options (temperature, max_tokens, etc.)
    ) -> Any:  # Returns ChatResult
        """Execute a chat completion with the specified model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model identifier (e.g., "gpt-4", "claude-3")
            api_key_id: ID of the API key to use
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ChatResult object with the completion response
        """
        ...

    async def get_available_models(self, api_key_id: str) -> List[str]:
        """Get list of available models for the given API key.
        
        Args:
            api_key_id: ID of the API key to check models for
            
        Returns:
            List of model identifiers available with this key
        """
        ...

    def get_token_counts(
        self, client_name: str, usage: Any
    ) -> Any:  # Returns TokenUsage
        """Extract token usage information from provider response.
        
        Args:
            client_name: Name of the LLM provider
            usage: Provider-specific usage object
            
        Returns:
            Standardized TokenUsage object
        """
        ...