"""Interface for LLM service."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.shared.domain import TokenUsage


class ILLMService(ABC):
    """Interface for LLM operations."""
    
    @abstractmethod
    def get_token_counts(self, client_name: str, usage: Any) -> TokenUsage:
        """Get token usage counts from LLM response."""
        pass
    
    @abstractmethod
    async def call_llm(
        self,
        service: Optional[str],
        api_key_id: str,
        model: str,
        messages: Any,  # Union[str, List[dict]]
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """Call an LLM with the given parameters."""
        pass
    
    @abstractmethod
    def pre_initialize_model(self, service: str, model: str, api_key_id: str) -> bool:
        """Pre-initialize a model to reduce first-call latency."""
        pass
    
    @abstractmethod
    async def get_available_models(self, service: str, api_key_id: str) -> List[str]:
        """Get list of available models for a service."""
        pass