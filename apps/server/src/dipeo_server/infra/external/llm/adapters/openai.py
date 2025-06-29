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

        # Combine cacheable and user prompts using the helper method
        combined_prompt = self._combine_prompts(cacheable_prompt, user_prompt)
        if combined_prompt:
            msgs.append({"role": "user", "content": combined_prompt})

        # Handle citation_target if needed
        if citation_target:
            msgs.append(
                {"role": "user", "content": f"Citation target: {citation_target}"}
            )

        return msgs

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> Any:
        params = {"model": self.model_name, "input": messages}
        for opt in ("temperature", "max_tokens", "n", "top_p"):
            if opt in kwargs and kwargs[opt] is not None:
                params[opt] = kwargs[opt]
        return self.client.responses.create(**params)

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        choice = response.choices[0] if response.choices else None
        return getattr(choice.message, "content", "") if choice else ""

    def _extract_usage_from_response(self, response: Any) -> dict[str, int]:
        u = getattr(response, "usage", None)
        return (
            {
                "prompt_tokens": getattr(u, "prompt_tokens", 0),
                "completion_tokens": getattr(u, "completion_tokens", 0),
                "total_tokens": getattr(u, "total_tokens", 0),
            }
            if u
            else {}
        )

    def list_models(self) -> list[str]:
        models = self.client.models.list().data
        return [m.id for m in models if "gpt" in m.id]
