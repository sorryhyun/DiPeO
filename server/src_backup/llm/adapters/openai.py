# openai_adapter.py
import openai
from openai import OpenAI
from typing import Any, Dict, List
from ..base import BaseAdapter, ChatResult

class ChatGPTAdapter(BaseAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str = ''
    ) -> List[Dict[str, str]]:
        msgs: List[Dict[str, str]] = []
        if system_prompt:
            msgs.append({'role': 'system', 'content': system_prompt})
        if user_prompt:
            msgs.append({'role': 'user', 'content': user_prompt})
        return msgs

    def _make_api_call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Any:
        params = {'model': self.model_name, 'messages': messages}
        for opt in ('temperature', 'max_tokens', 'n', 'top_p'):
            if opt in kwargs and kwargs[opt] is not None:
                params[opt] = kwargs[opt]
        return self.client.chat.completions.create(**params)

    def _extract_text(self, response: Any) -> str:
        choice = response.choices[0] if response.choices else None
        return getattr(choice.message, 'content', '') if choice else ''

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        u = getattr(response, 'usage', None)
        return {
            'prompt_tokens': getattr(u, 'prompt_tokens', 0),
            'completion_tokens': getattr(u, 'completion_tokens', 0),
            'total_tokens': getattr(u, 'total_tokens', 0)
        } if u else {}

    def list_models(self) -> List[str]:
        models = self.client.models.list().data
        return [m.id for m in models if 'gpt' in m.id]
