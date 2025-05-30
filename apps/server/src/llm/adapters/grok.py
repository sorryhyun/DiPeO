import anthropic
from ..base import BaseAdapter, ChatResult


class GrokAdapter(BaseAdapter):
    """Adapter for Grok models via the Anthropic API."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name)
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url or "https://api.x.ai")

    def _grok_text_blocks(self,
                          cacheable_prompt: str = '',
                          user_prompt: str = '',
                          citation_target: str | None = None) -> list[dict]:
        """Build a list of Grok message blocks for user content."""
        blocks: list[dict] = []
        if cacheable_prompt: pass
        if user_prompt:
            blocks.append({'type': 'text', 'text': cacheable_prompt + user_prompt})
        if citation_target:
            raise NotImplementedError("Citation not supported in Grok adapter")
        return blocks

    def chat(self, system_prompt: str, cacheable_prompt: str = '', user_prompt: str = '', citation_target: str = '',
             **kwargs) -> ChatResult:  # noqa: E501
        try:
            blocks = self._grok_text_blocks(
                cacheable_prompt=cacheable_prompt,
                user_prompt=user_prompt,
                citation_target=citation_target
            )
            messages_input = [{'role': 'user', 'content': blocks}]
            if kwargs.get('prefill'):
                messages_input.append({'role': 'assistant', 'content': [{'type': 'text', 'text': kwargs['prefill']}]})
            message = self.client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=messages_input,
                max_tokens=kwargs.get('max_tokens'),
                temperature=kwargs.get('temperature'),
                # tools=kwargs.get('tools'),
            )
            
            text = message.content[0].text if message.content else ''
            return ChatResult(
                text=text,
                usage=message.usage,
                raw_response=message
            )
        except Exception as e:
            return ChatResult(text='', usage=None)

    def list_models(self) -> list[str]:
        """List available Grok models."""
        # Grok doesn't provide a models.list() API, so return known models
        return [
            "grok-2-latest",
            "grok-2-vision-1212",
            "grok-beta"
        ]