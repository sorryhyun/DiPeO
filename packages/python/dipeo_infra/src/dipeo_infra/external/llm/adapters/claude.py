import anthropic
from dipeo_domain import ChatResult, TokenUsage

from ..base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models."""

    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize the Anthropic client."""
        return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call to Claude and return ChatResult."""
        # Convert standard messages format to Claude format
        system_prompt = ""
        claude_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "assistant":
                claude_messages.append({"role": "assistant", "content": content})
            else:  # user role
                claude_messages.append({"role": "user", "content": content})

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

        # Extract allowed parameters
        allowed_params = ["max_tokens", "temperature", "tools"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

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

        # Extract usage
        prompt_tokens = None
        completion_tokens = None

        if hasattr(response, "usage") and response.usage:
            prompt_tokens = getattr(response.usage, "input_tokens", None)
            completion_tokens = getattr(response.usage, "output_tokens", None)

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
