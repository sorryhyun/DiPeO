import anthropic
import google.generativeai as genai
from google.generativeai import types
from openai import OpenAI
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ChatResult:
    """Unified result type for all LLM adapters."""
    text: str
    usage: Optional[Any] = None  # Provider-specific usage object
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_response: Optional[Any] = None  # Original provider response


class BaseAdapter:
    """Base interface for LLM adapters."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def chat(self, system_prompt: str, cacheable_prompt: str = '', user_prompt: str = '', citation_target: str = '',
             **kwargs) -> ChatResult:  # noqa: E501
        raise NotImplementedError


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


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via the genai API."""

    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.client = genai.Client(api_key=api_key)

    def chat(self, system_prompt: str, cacheable_prompt: str = '', user_prompt: str = '', **kwargs) -> ChatResult:  # noqa: E501
        try:
            message_content = [{"role": "user", "parts": [{'text': user_prompt}]}]
            if kwargs.get('prefill'):
                message_content.append({"role": "model", "parts": [{'text': kwargs['prefill'].rstrip().rstrip('\n')}]})
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=kwargs.get('max_tokens'),
                    temperature=kwargs.get('temperature'),
                    thinking_config=types.ThinkingConfig(thinking_budget=1024),
                    safety_settings=kwargs.get('gemini_safety_settings'),
                ),
                contents=message_content,
            )
            
            return ChatResult(
                text=response.text if hasattr(response, 'text') else '',
                usage=None,  # Gemini doesn't provide usage in the same format
                prompt_tokens=response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                completion_tokens=response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
                raw_response=response
            )
        except Exception as e:
            return ChatResult(text='', usage=None)


class ChatGPTAdapter(BaseAdapter):

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _build_messages(self, system_prompt: str = '', cacheable_prompt: str = '', 
                       user_prompt: str = '', **kwargs) -> list[dict]:
        """Build proper OpenAI message format."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        combined_prompt = ""
        if cacheable_prompt:
            combined_prompt += cacheable_prompt
        if user_prompt:
            if combined_prompt:
                combined_prompt += "\n\n" + user_prompt
            else:
                combined_prompt = user_prompt
        
        if combined_prompt:
            messages.append({"role": "user", "content": combined_prompt})
        
        if kwargs.get('prefill'):
            messages.append({
                "role": "assistant",
                "content": kwargs['prefill'].rstrip()
            })
        
        return messages

    def chat(self, system_prompt: str = '', cacheable_prompt: str = '', 
             user_prompt: str = '', **kwargs) -> ChatResult:
        """Make OpenAI chat completion call."""
        try:
            messages = self._build_messages(
                system_prompt=system_prompt,
                cacheable_prompt=cacheable_prompt,
                user_prompt=user_prompt,
                **kwargs
            )
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens'),
                temperature=kwargs.get('temperature'),
                tools=kwargs.get('tools'),
                tool_choice=kwargs.get('tool_choice')
            )
            
            text = ''
            if response.choices:
                message_content = response.choices[0].message
                if kwargs.get('tools') and message_content.tool_calls:
                    text = message_content.tool_calls[0].function.arguments
                else:
                    text = message_content.content or ""
            
            return ChatResult(
                text=text,
                usage=response.usage,
                raw_response=response
            )
            
        except Exception as e:
            return ChatResult(text='', usage=None)