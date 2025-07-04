import logging

import anthropic
from dipeo_domain import ChatResult, TokenUsage

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class GrokAdapter(BaseAdapter):
    """Adapter for Grok models via the Anthropic API."""

    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize the Anthropic client for Grok."""
        base_url = self.base_url or "https://api.x.ai"
        return anthropic.Anthropic(api_key=self.api_key, base_url=base_url)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Anthropic format with content blocks
        anthropic_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            anthropic_messages.append(
                {"role": role, "content": [{"type": "text", "text": content}]}
            )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature"])

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

        # Use base method to create token usage
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
        )
