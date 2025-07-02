# openai_adapter.py

from dipeo_domain import ChatResult, TokenUsage
from openai import OpenAI

from ..base import BaseAdapter


class ChatGPTAdapter(BaseAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        # Map roles for OpenAI compatibility
        mapped_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # OpenAI uses "developer" role instead of "system" in newer models
            if role == "system" and "o1" in self.model_name:
                role = "developer"
            mapped_messages.append({"role": role, "content": msg.get("content", "")})

        # Extract allowed parameters
        allowed_params = ["temperature", "max_tokens", "n", "top_p"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        # Make API call
        params = {"model": self.model_name, "messages": mapped_messages, **api_params}
        response = self.client.chat.completions.create(**params)

        # Extract response data
        text = ""
        if response.choices:
            text = response.choices[0].message.content or ""

        # Extract usage
        prompt_tokens = None
        completion_tokens = None

        if hasattr(response, "usage") and response.usage:
            prompt_tokens = getattr(response.usage, "prompt_tokens", None)
            completion_tokens = getattr(response.usage, "completion_tokens", None)

        # Create TokenUsage if we have usage data
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            token_usage = TokenUsage(
                input=prompt_tokens or 0,
                output=completion_tokens or 0,
                total=(prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None and completion_tokens is not None
                else None,
            )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
        )
