"""Domain ports for LLM services."""

from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.diagram_generated import ChatResult, Message, PersonLLMConfig, TokenUsage
    from dipeo.diagram_generated.domain_models import PersonID


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client operations across providers."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        **kwargs,
    ) -> "ChatResult":
        """Complete a chat prompt."""
        ...

    async def complete_with_person(
        self,
        person_messages: list["Message"],
        person_id: "PersonID",
        llm_config: "PersonLLMConfig",
        **kwargs,
    ) -> "ChatResult":
        """Complete a prompt with person-specific context and system prompt handling."""
        ...

    async def get_available_models(self, api_key_id: str) -> list[str]:
        """Get list of available models for the provider."""
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


@runtime_checkable
class LLMService(Protocol):
    """High-level LLM service for provider selection and enrichment."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
        **kwargs,
    ) -> "ChatResult":
        """Complete with automatic provider selection."""
        ...

    async def complete_with_person(
        self,
        person_messages: list["Message"],
        person_id: "PersonID",
        llm_config: Optional["PersonLLMConfig"] = None,
        **kwargs,
    ) -> "ChatResult":
        """Complete with person context, memory enrichment, and provider selection."""
        ...

    async def validate_api_key(
        self, api_key_id: str, provider: Optional[str] = None
    ) -> bool:
        """Validate an API key is functional."""
        ...

    async def get_provider_for_model(self, model: str) -> Optional[str]:
        """Determine which provider supports a given model."""
        ...


@runtime_checkable
class MemoryService(Protocol):
    """Service for managing conversation memory and context."""

    async def get_relevant_memory(
        self,
        person_id: "PersonID",
        messages: list["Message"],
        limit: int = 10,
    ) -> list["Message"]:
        """Retrieve relevant memory for context."""
        ...

    async def store_interaction(
        self,
        person_id: "PersonID",
        messages: list["Message"],
        response: "ChatResult",
    ) -> None:
        """Store interaction in memory."""
        ...

    async def clear_memory(self, person_id: "PersonID") -> None:
        """Clear all memory for a person."""
        ...