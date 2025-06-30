# openai_adapter.py
from typing import Any

from openai import OpenAI

from ..base import BaseAdapter


class ChatGPTAdapter(BaseAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_messages(
        self,
        system_prompt: str,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = "",
        **kwargs,
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})

        # Use base class helper to build user message content
        user_content = self._build_user_message_content(
            cacheable_prompt, user_prompt, citation_target
        )
        if user_content:
            msgs.append({"role": "user", "content": user_content})

        # Handle prefill if provided
        if kwargs.get("prefill"):
            self._handle_prefill(msgs, kwargs["prefill"])

        return msgs

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> Any:
        # Use base class helper to extract allowed parameters
        allowed_params = ["temperature", "max_tokens", "n", "top_p"]
        api_params = self._extract_api_params(kwargs, allowed_params)

        params = {"model": self.model_name, "messages": messages, **api_params}
        return self.client.chat.completions.create(**params)

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        choice = response.choices[0] if response.choices else None
        return getattr(choice.message, "content", "") if choice else ""

    def _extract_usage_from_response(self, response: Any) -> dict[str, int]:
        # Use base class helper with OpenAI's field names
        usage_obj = getattr(response, "usage", None)
        return self._extract_usage_safely(
            usage_obj,
            input_field="prompt_tokens",
            output_field="completion_tokens"
        )

    def list_models(self) -> list[str]:
        models = self.client.models.list().data
        return [m.id for m in models if "gpt" in m.id]
