from openai import OpenAI
from typing import Any, Dict, List, Optional
import logging
from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class ChatGPTAdapter(BaseAdapter):
    """Adapter for OpenAI GPT models using the new responses SDK."""

    def _initialize_client(self) -> OpenAI:
        """Initialize the OpenAI client."""
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_messages(self, system_prompt: str, cacheable_prompt: str = '',
                        user_prompt: str = '', citation_target: str = '',
                        **kwargs) -> List[Dict]:
        """Build provider-specific message format for responses SDK."""
        messages = []

        # Use 'developer' role instead of 'system' for the new SDK
        if system_prompt:
            messages.append({"role": "developer", "content": system_prompt})

        # Use base class helper to combine prompts
        combined_prompt = self._combine_prompts(cacheable_prompt, user_prompt)

        if combined_prompt:
            messages.append({"role": "user", "content": combined_prompt})

        # Handle prefill - adjust role if needed for new SDK
        if kwargs.get('prefill'):
            prefill_msg = self._build_prefill_message(kwargs['prefill'])
            # Update assistant role to model role if needed by new SDK
            if prefill_msg.get('role') == 'assistant':
                prefill_msg['role'] = 'model'
            messages.append(prefill_msg)

        return messages

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        # New SDK uses response.output_text directly
        if hasattr(response, 'output_text'):
            return response.output_text or ""

        # Fallback for tool responses if the structure changes
        if kwargs.get('tools') and hasattr(response, 'tool_outputs'):
            # Adjust based on actual tool output structure in new SDK
            return str(response.tool_outputs[0]) if response.tool_outputs else ""

        return ''

    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from provider-specific response."""
        # Check if new SDK still provides usage metadata
        if hasattr(response, 'usage'):
            usage = response.usage
            return {
                'prompt_tokens': getattr(usage, 'prompt_tokens', None),
                'completion_tokens': getattr(usage, 'completion_tokens', None),
                'total_tokens': getattr(usage, 'total_tokens', None)
            }
        # New SDK might have different usage structure
        elif hasattr(response, 'token_usage'):
            usage = response.token_usage
            return {
                'prompt_tokens': getattr(usage, 'input_tokens', None),
                'completion_tokens': getattr(usage, 'output_tokens', None),
                'total_tokens': getattr(usage, 'total_tokens', None)
            }
        return None

    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider using new responses SDK."""
        # Use responses.create instead of chat.completions.create
        api_params = {
            'model': self.model_name,
            'input': messages,  # Changed from 'messages' to 'input'
        }

        # Add optional parameters if provided
        if kwargs.get('max_tokens'):
            api_params['max_tokens'] = kwargs['max_tokens']

        if kwargs.get('temperature') is not None:
            api_params['temperature'] = kwargs['temperature']

        # Handle tools in new format
        if kwargs.get('tools'):
            # Convert old tool format to new format if needed
            # Example: [{"type": "function", "function": {...}}] -> [{"type": "web_search_preview"}]
            tools = kwargs['tools']
            # If tools are in old format, you might need to transform them
            # For now, pass them through
            api_params['tools'] = tools

            if kwargs.get('tool_choice'):
                api_params['tool_choice'] = kwargs['tool_choice']

        return self.client.responses.create(**api_params)

    def list_models(self) -> List[str]:
        """List available OpenAI models."""
        logger.info("[OpenAI] Fetching available models from OpenAI API")
        try:
            # Check if models.list() still works with new SDK
            models = self.client.models.list()
            # Filter for models that work with responses SDK
            response_models = [
                model.id for model in models.data
                if 'gpt' in model.id.lower() or model.id.startswith('o1')
            ]
            logger.info(f"[OpenAI] Found {len(response_models)} response models")
            return sorted(response_models)
        except Exception as e:
            logger.error(f"[OpenAI] Failed to fetch models from API: {str(e)}")
            # Use base class fallback models
            return super().list_models()

    def supports_tools(self) -> bool:
        """Check if this adapter supports tool/function calling."""
        return True

    def chat_with_messages(self, messages: List[Dict[str, str]], **kwargs) -> 'ChatResult':
        """
        Override to handle the new SDK format for conversation history.
        """
        try:
            # For conversation history, we might need to ensure proper role mapping
            adjusted_messages = []
            for msg in messages:
                adjusted_msg = msg.copy()
                # Map old roles to new roles
                if adjusted_msg.get('role') == 'system':
                    adjusted_msg['role'] = 'developer'
                elif adjusted_msg.get('role') == 'assistant':
                    # Check if new SDK uses 'model' or keeps 'assistant'
                    adjusted_msg['role'] = 'model'
                adjusted_messages.append(adjusted_msg)

            # Make the API call with adjusted messages
            print(adjusted_messages)
            response = self.client.responses.create(
                model=self.model_name,
                input=adjusted_messages,
                **kwargs
            )

            # Extract results using new response format
            text = self._extract_text_from_response(response, **kwargs)
            usage_dict = self._extract_usage_from_response(response)

            from ..base import ChatResult
            return ChatResult(
                text=text,
                usage=response if hasattr(response, 'usage') or hasattr(response, 'token_usage') else None,
                prompt_tokens=usage_dict.get('prompt_tokens') if usage_dict else None,
                completion_tokens=usage_dict.get('completion_tokens') if usage_dict else None,
                total_tokens=usage_dict.get('total_tokens') if usage_dict else None,
                raw_response=response
            )

        except Exception as e:
            logger.error(f"LLM call with messages failed for {self.__class__.__name__}: {str(e)}")
            from ..base import ChatResult
            return ChatResult(text='', usage=None)