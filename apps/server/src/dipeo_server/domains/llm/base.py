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
        return any(
            v is not None
            for v in (self.prompt_tokens, self.completion_tokens, self.total_tokens)
        )
    
    @property
    def usage(self) -> Optional[Dict[str, int]]:
        if self.has_usage:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }
        return None


class BaseAdapter(ABC):

    FALLBACK_MODELS: Dict[str, List[str]] = {"openai": ["gpt-4", "gpt-3.5-turbo"]}

    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

    def _combine_prompts(self, cacheable_prompt: str, user_prompt: str) -> str:
        parts = [p for p in [cacheable_prompt, user_prompt] if p]
        return "\n\n".join(parts) if parts else ""
    
    def _safe_strip_prefill(self, prefill: str) -> str:
        return prefill.strip() if prefill else ""

    @abstractmethod
    def _initialize_client(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _build_messages(
        self,
        system_prompt: str,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = "",
        **kwargs,
    ) -> Any:
        ...

    @abstractmethod
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        raise NotImplementedError

    def chat(self, system_prompt: str, user_prompt: str = "", **kwargs) -> ChatResult:
        msgs = self._build_messages(system_prompt, user_prompt=user_prompt, **kwargs)
        resp = self._make_api_call(msgs, system_prompt=system_prompt, **kwargs)
        text = self._extract_text_from_response(resp, **kwargs)
        usage = self._extract_usage_from_response(resp) or {}
        return ChatResult(
            text=text,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            raw_response=resp,
        )

    def chat_with_messages(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> ChatResult:
        resp = self._make_api_call(messages, **kwargs)
        text = self._extract_text_from_response(resp, **kwargs)
        usage = self._extract_usage_from_response(resp) or {}
        return ChatResult(
            text=text,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            raw_response=resp,
        )

    def list_models(self) -> List[str]:
        return self.FALLBACK_MODELS.get("openai", [])
