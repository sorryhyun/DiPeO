from openai import OpenAI
from typing import Any, Dict, List, Optional
import logging
from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class ChatGPTAdapter(BaseAdapter):
    """Adapter for OpenAI GPT models."""

    def _initialize_client(self) -> OpenAI:
        """Initialize the OpenAI client."""
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_messages(self, system_prompt: str, cacheable_prompt: str = '', 
                       user_prompt: str = '', citation_target: str = '', 
                       **kwargs) -> List[Dict]:
        """Build provider-specific message format."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Use base class helper to combine prompts
        combined_prompt = self._combine_prompts(cacheable_prompt, user_prompt)
        
        if combined_prompt:
            messages.append({"role": "user", "content": combined_prompt})
        
        # Handle prefill using base class helper
        if kwargs.get('prefill'):
            messages.append(self._build_prefill_message(kwargs['prefill']))
        
        return messages
    
    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        if response.choices:
            message_content = response.choices[0].message
            if kwargs.get('tools') and message_content.tool_calls:
                return message_content.tool_calls[0].function.arguments
            else:
                return message_content.content or ""
        return ''
    
    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from provider-specific response."""
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            return {
                'prompt_tokens': getattr(usage, 'prompt_tokens', None),
                'completion_tokens': getattr(usage, 'completion_tokens', None),
                'total_tokens': getattr(usage, 'total_tokens', None)
            }
        return None
    
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature'),
            tools=kwargs.get('tools'),
            tool_choice=kwargs.get('tool_choice')
        )
    
    def list_models(self) -> List[str]:
        """List available OpenAI models."""
        logger.info("[OpenAI] Fetching available models from OpenAI API")
        try:
            models = self.client.models.list()
            # Filter for chat models and sort by name
            chat_models = [
                model.id for model in models.data 
                if 'gpt' in model.id.lower() or 'text' in model.id.lower()
            ]
            logger.info(f"[OpenAI] Found {len(chat_models)} chat models")
            return sorted(chat_models)
        except Exception as e:
            logger.error(f"[OpenAI] Failed to fetch models from API: {str(e)}")
            # Use base class fallback models
            return super().list_models()
    
    def supports_tools(self) -> bool:
        """Check if this adapter supports tool/function calling."""
        return True