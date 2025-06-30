from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ChatResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw_response: Any | None = None

    @property
    def has_usage(self) -> bool:
        return any(
            v is not None
            for v in (self.prompt_tokens, self.completion_tokens, self.total_tokens)
        )

    @property
    def usage(self) -> dict[str, int | None] | None:
        if self.has_usage:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }
        return None


class BaseAdapter(ABC):
    FALLBACK_MODELS: dict[str, list[str]] = {"openai": ["gpt-4", "gpt-3.5-turbo"]}

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

    def _combine_prompts(self, cacheable_prompt: str, user_prompt: str) -> str:
        parts = [p for p in [cacheable_prompt, user_prompt] if p]
        return "\n\n".join(parts) if parts else ""

    def _safe_strip_prefill(self, prefill: str) -> str:
        return prefill.strip() if prefill else ""

    def _extract_usage_safely(
        self,
        usage_obj: Any,
        input_field: str = "input_tokens",
        output_field: str = "output_tokens"
    ) -> dict[str, int | None]:
        """Safely extract token usage from provider response objects."""
        if not usage_obj:
            return {}

        prompt_tokens = getattr(usage_obj, input_field, None)
        completion_tokens = getattr(usage_obj, output_field, None)

        result = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

        # Calculate total if both values exist
        if prompt_tokens is not None and completion_tokens is not None:
            result["total_tokens"] = prompt_tokens + completion_tokens
        else:
            result["total_tokens"] = None

        return result

    def _build_user_message_content(
        self,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = ""
    ) -> str:
        """Build combined user message content."""
        combined = self._combine_prompts(cacheable_prompt, user_prompt)
        if citation_target:
            combined += f"\n\nCitation target: {citation_target}"
        return combined

    def _handle_prefill(
        self,
        messages: list[dict[str, str]],
        prefill: str,
        assistant_role: str = "assistant"
    ) -> list[dict[str, str]]:
        """Add prefill message if provided."""
        if prefill:
            prefill_text = self._safe_strip_prefill(prefill)
            messages.append({"role": assistant_role, "content": prefill_text})
        return messages

    def _extract_api_params(
        self,
        kwargs: dict[str, Any],
        allowed_params: list[str]
    ) -> dict[str, Any]:
        """Extract only allowed parameters for API calls."""
        return {k: v for k, v in kwargs.items()
                if k in allowed_params and v is not None}

    def _safe_extract_text(
        self,
        response: Any,
        default: str = "",
        **kwargs
    ) -> str:
        """Safely extract text with fallback."""
        try:
            return self._extract_text_from_response(response, **kwargs)
        except (AttributeError, IndexError, TypeError):
            return default

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
    ) -> Any: ...

    @abstractmethod
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def _extract_usage_from_response(self, response: Any) -> dict[str, int] | None:
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
        self, messages: list[dict[str, str]], **kwargs
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

    def list_models(self) -> list[str]:
        return self.FALLBACK_MODELS.get("openai", [])
