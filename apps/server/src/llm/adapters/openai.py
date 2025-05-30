from openai import OpenAI
from ..base import BaseAdapter, ChatResult


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