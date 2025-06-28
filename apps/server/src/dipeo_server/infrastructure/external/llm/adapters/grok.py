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

        # Use base class helper to combine prompts
        combined_prompt = self._combine_prompts(cacheable_prompt, user_prompt)

        messages = []
        if combined_prompt:
            messages.append(
                {"role": "user", "content": [{"type": "text", "text": combined_prompt}]}
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
        if hasattr(response, "usage"):
            usage = response.usage
            return {
                "prompt_tokens": getattr(usage, "input_tokens", None),
                "completion_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": (
                    getattr(usage, "input_tokens", 0)
                    + getattr(usage, "output_tokens", 0)
                ),
            }
        return None

    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        # Extract system prompt from kwargs since it's passed from base class chat method
        system_prompt = kwargs.get("system_prompt", "")

        return self.client.messages.create(
            model=self.model_name,
            system=system_prompt,
            messages=messages,
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
            # tools not supported by Grok
        )
