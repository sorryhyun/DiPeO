import anthropic
from ..base import BaseAdapter, ChatResult


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name)
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)

    def _anthropic_text_blocks(self,
                               cacheable_prompt: str = '',
                               user_prompt: str = '',
                               citation_target: str | None = None) -> list[dict]:
        """Build a list of Anthropic message blocks for user content."""
        blocks: list[dict] = []
        if cacheable_prompt:
            blocks.append({
                'type': 'text',
                'text': cacheable_prompt,
                'cache_control': {'type': 'ephemeral'}
            })
        if user_prompt:
            blocks.append({'type': 'text', 'text': user_prompt})
        if citation_target:
            blocks.append({
                'type': 'document',
                'source': {'type': 'text', 'media_type': 'text/plain', 'data': citation_target},
                'title': 'Document to cite',
                'context': 'Document to cite',
                'citations': {'enabled': True}
            })
        return blocks

    def _build_former(self, cacheable_prompt: str = '', user_prompt: str = '', citation_target: str = '', **kwargs):
        blocks = self._anthropic_text_blocks(
            cacheable_prompt=cacheable_prompt,
            user_prompt=user_prompt,
            citation_target=citation_target
        )
        input_target = [{'role': 'user', 'content': blocks}]
        if kwargs.get('prefill'):
            input_target.append({
                'role': 'assistant',
                'content': kwargs['prefill'].rstrip().rstrip('\n')
            })
        return input_target

    def chat(self, system_prompt: str, cacheable_prompt: str = '',
             user_prompt: str = '', citation_target: str = '', **kwargs) -> ChatResult:  # noqa: E501
        try:
            message = self.client.messages.create(
                model=self.model_name,
                system=[{'type': 'text', 'text': system_prompt, 'cache_control': {'type': 'ephemeral'}}],
                messages= self._build_former(
                    cacheable_prompt=cacheable_prompt, user_prompt=user_prompt,
                    citation_target=citation_target, **kwargs),
                max_tokens=kwargs.get('max_tokens'),
                # tool_choice=kwargs.get('tool_choice'),
                temperature=kwargs.get('temperature'),
                tools=kwargs.get('tools'),
            )
            if kwargs.get('on_one', False): idx = 1
            else:idx = 0
            
            text = ''
            if kwargs.get('tools') and hasattr(message.content[idx], 'input'):
                text = message.content[idx].input
            elif hasattr(message.content[idx], 'text'):
                text = message.content[idx].text
            
            return ChatResult(
                text=text,
                usage=message.usage,
                raw_response=message
            )
        except Exception as e:
            return ChatResult(text='', usage=None)

    def list_models(self) -> list[str]:
        """List available Claude models."""
        # Anthropic doesn't provide a models.list() API, so return known models
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]