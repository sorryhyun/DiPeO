import logging
from typing import Any

import anthropic

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class GrokAdapter(BaseAdapter):
    """Adapter for Grok models via the Anthropic API."""

    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize the Anthropic client for Grok."""
        base_url = self.base_url or "https://api.x.ai"
        return anthropic.Anthropic(api_key=self.api_key, base_url=base_url)

    def _build_messages(
        self,
        system_prompt: str,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = "",
        **kwargs,
    ) -> list[dict]:
        """Build provider-specific message format."""
        if citation_target:
            raise NotImplementedError("Citation not supported in Grok adapter")

        # Use base class helper to build user message content
        user_content = self._build_user_message_content(
            cacheable_prompt, user_prompt, ""  # No citation support
        )

        messages = []
        if user_content:
            messages.append(
                {"role": "user", "content": [{"type": "text", "text": user_content}]}
            )

        # Handle prefill
        if kwargs.get("prefill"):
            prefill_text = self._safe_strip_prefill(kwargs["prefill"])
            messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": prefill_text}],
                }
            )

        return messages

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        if response.content and len(response.content) > 0:
            return response.content[0].text
        return ""

    def _extract_usage_from_response(self, response: Any) -> dict[str, int] | None:
        """Extract token usage from provider-specific response."""
        usage_obj = getattr(response, "usage", None)
        return self._extract_usage_safely(
            usage_obj,
            input_field="input_tokens",
            output_field="output_tokens"
        )

    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        # Extract system prompt from kwargs since it's passed from base class chat method
        system_prompt = kwargs.get("system_prompt", "")

        # Use base class helper to extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = self._extract_api_params(kwargs, allowed_params)

        return self.client.messages.create(
            model=self.model_name,
            system=system_prompt,
            messages=messages,
            **api_params
            # tools not supported by Grok
        )
