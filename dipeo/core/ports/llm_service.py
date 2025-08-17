"""LLM Service port interface.

DEPRECATED: This module re-exports domain types for backward compatibility.
Use dipeo.domain.llm directly for new code.
"""

import warnings
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

# Re-export domain types
from dipeo.domain.llm import LLMClient, LLMService, MemoryService

if TYPE_CHECKING:
    from dipeo.diagram_generated import ChatResult, Message, PersonLLMConfig, TokenUsage
    from dipeo.diagram_generated.domain_models import PersonID

warnings.warn(
    "dipeo.core.ports.llm_service is deprecated. "
    "Use dipeo.domain.llm instead.",
    DeprecationWarning,
    stacklevel=2,
)


@runtime_checkable
class LLMServicePort(Protocol):
    """Legacy LLM service port - wraps new domain LLMClient for backward compatibility."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        **kwargs,
    ) -> "ChatResult":
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


# Export domain types for backward compatibility
__all__ = [
    "LLMServicePort",
    "LLMClient",
    "LLMService",
    "MemoryService",
]