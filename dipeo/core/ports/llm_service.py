"""LLM Service port interface."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.models import ChatResult, TokenUsage


@runtime_checkable
class LLMServicePort(Protocol):
    """Port for LLM service operations across providers (OpenAI, Claude, Gemini, etc.)."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        **kwargs,
    ) -> "ChatResult":
        ...

    async def get_available_models(self, api_key_id: str) -> list[str]:
        ...

    def get_token_counts(
        self, client_name: str, usage: Any
    ) -> "TokenUsage":
        """Extract token usage information from provider response.
        
        Args:
            client_name: Name of the LLM provider
            usage: Provider-specific usage object
            
        Returns:
            Standardized TokenUsage object
        """
        ...