import google.generativeai as genai
from google.generativeai import types
from ..base import BaseAdapter, ChatResult


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