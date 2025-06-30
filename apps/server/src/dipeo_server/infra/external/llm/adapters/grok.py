import logging

import anthropic

from ..base import BaseAdapter, ChatResult

logger = logging.getLogger(__name__)


class GrokAdapter(BaseAdapter):
    """Adapter for Grok models via the Anthropic API."""

    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize the Anthropic client for Grok."""
        base_url = self.base_url or "https://api.x.ai"
        return anthropic.Anthropic(api_key=self.api_key, base_url=base_url)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call to Grok and return ChatResult."""
        # Extract system prompt and convert messages to Anthropic format
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role in ["user", "assistant"]:
                # Grok uses Anthropic's message format with content blocks
                anthropic_messages.append(
                    {"role": role, "content": [{"type": "text", "text": content}]}
                )

        # Extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        # Make the API call
        response = self.client.messages.create(
            model=self.model_name,
            system=system_prompt,
            messages=anthropic_messages,
            **api_params,
            # tools not supported by Grok
        )

        # Extract text
        text = ""
        if response.content and len(response.content) > 0:
            text = response.content[0].text

        # Extract usage
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

        usage_obj = getattr(response, "usage", None)
        if usage_obj:
            prompt_tokens = getattr(usage_obj, "input_tokens", None)
            completion_tokens = getattr(usage_obj, "output_tokens", None)
            if prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens

        return ChatResult(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response=response,
        )
