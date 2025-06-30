from typing import Any

import anthropic

from ..base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models."""

    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize the Anthropic client."""
        return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)

    def _anthropic_text_blocks(
        self,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str | None = None,
    ) -> list[dict]:
        """Build a list of Anthropic message blocks for user content."""
        blocks: list[dict] = []
        if cacheable_prompt:
            blocks.append(
                {
                    "type": "text",
                    "text": cacheable_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        if user_prompt:
            blocks.append({"type": "text", "text": user_prompt})
        if citation_target:
            blocks.append(
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": citation_target,
                    },
                    "title": "Document to cite",
                    "context": "Document to cite",
                    "citations": {"enabled": True},
                }
            )
        return blocks

    def _build_messages(
        self,
        system_prompt: str,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = "",
        **kwargs,
    ) -> dict[str, Any]:
        """Build provider-specific message format."""
        blocks = self._anthropic_text_blocks(
            cacheable_prompt=cacheable_prompt,
            user_prompt=user_prompt,
            citation_target=citation_target,
        )
        messages = [{"role": "user", "content": blocks}]

        # Handle prefill
        if kwargs.get("prefill"):
            messages.append(self._build_prefill_message(kwargs["prefill"]))

        # Return both system and messages for Claude API
        return {
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
        }

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        idx = 1 if kwargs.get("on_one", False) else 0

        if kwargs.get("tools") and hasattr(response.content[idx], "input"):
            return response.content[idx].input
        if hasattr(response.content[idx], "text"):
            return response.content[idx].text

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
        # Use base class helper to extract allowed parameters
        allowed_params = ["max_tokens", "temperature", "tools"]
        api_params = self._extract_api_params(kwargs, allowed_params)

        return self.client.messages.create(
            model=self.model_name,
            system=messages["system"],
            messages=messages["messages"],
            **api_params
        )

    def supports_tools(self) -> bool:
        """Check if this adapter supports tool/function calling."""
        return True

    def supports_citations(self) -> bool:
        """Check if this adapter supports citations."""
        return True
