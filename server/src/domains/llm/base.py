# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ChatResult:
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_response: Optional[Any] = None

    @property
    def has_usage(self) -> bool:
        return any(v is not None for v in (
            self.prompt_tokens, self.completion_tokens, self.total_tokens
        ))
    
    @property
    def usage(self) -> Dict[str, int]:
        """Return usage stats as a dict for compatibility."""
        return {
            'prompt_tokens': self.prompt_tokens or 0,
            'completion_tokens': self.completion_tokens or 0,
            'total_tokens': self.total_tokens or 0
        }

class BaseAdapter(ABC):
    """Minimal interface for an LLM adapter."""

    FALLBACK_MODELS: Dict[str, List[str]] = {
        'openai': ['gpt-4', 'gpt-3.5-turbo']
    }

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""
        raise NotImplementedError

    @abstractmethod
    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str = ''
    ) -> List[Dict[str, str]]:
        ...

    @abstractmethod
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        raise NotImplementedError

    @abstractmethod
    def _extract_text(self, response: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    def _extract_usage(self, response: Any) -> Dict[str, int]:
        raise NotImplementedError

    def chat(
        self,
        system_prompt: str,
        user_prompt: str = '',
        **kwargs
    ) -> ChatResult:
        msgs = self._build_messages(system_prompt, user_prompt)
        resp = self._make_api_call(msgs, **kwargs)
        text = self._extract_text(resp)
        usage = self._extract_usage(resp)
        return ChatResult(
            text=text,
            prompt_tokens=usage.get('prompt_tokens'),
            completion_tokens=usage.get('completion_tokens'),
            total_tokens=usage.get('total_tokens'),
            raw_response=resp
        )

    def chat_with_messages(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ChatResult:
        """Chat with pre-built messages array (for conversation history)."""
        resp = self._make_api_call(messages, **kwargs)
        text = self._extract_text(resp)
        usage = self._extract_usage(resp)
        return ChatResult(
            text=text,
            prompt_tokens=usage.get('prompt_tokens'),
            completion_tokens=usage.get('completion_tokens'),
            total_tokens=usage.get('total_tokens'),
            raw_response=resp
        )

    def list_models(self) -> List[str]:
        return self.FALLBACK_MODELS.get('openai', [])