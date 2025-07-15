import anthropic

from dipeo.models import ChatResult

from ..base import BaseLLMAdapter


class ClaudeAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models."""

    def _initialize_client(self) -> anthropic.Anthropic:
        return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        system_prompt, claude_messages = self._extract_system_and_messages(messages)

        # Build system blocks with caching
        system_blocks = []
        if system_prompt:
            system_blocks.append(
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "tools"])

        # Make API call
        response = self.client.messages.create(
            model=self.model_name,
            system=system_blocks,
            messages=claude_messages,
            **api_params,
        )

        # Extract text from response
        text = ""
        if response.content:
            # Handle tool calls or regular text
            idx = 1 if kwargs.get("on_one", False) else 0
            if idx < len(response.content):
                content_block = response.content[idx]
                if kwargs.get("tools") and hasattr(content_block, "input"):
                    text = content_block.input
                elif hasattr(content_block, "text"):
                    text = content_block.text

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