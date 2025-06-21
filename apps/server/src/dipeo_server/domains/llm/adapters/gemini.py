import google.genai as genai
from typing import Any, Dict, List, Optional
import logging
from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via the genai API."""

    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        # Gemini doesn't use base_url, but we accept it for consistency
        super().__init__(model_name, api_key, base_url)

    def _initialize_client(self) -> Any:
        """Initialize the Gemini client."""
        # Configure the API key globally for google-generativeai
        genai.configure(api_key=self.api_key)
        # Return None as genai uses state configuration
        return None

    def _build_messages(self, system_prompt: str, cacheable_prompt: str = '', 
                       user_prompt: str = '', citation_target: str = '', 
                       **kwargs) -> Dict[str, Any]:
        """Build provider-specific message format."""
        # Use base class helper to combine prompts
        combined_prompt = self._combine_prompts(cacheable_prompt, user_prompt)
        
        message_content = [{"role": "user", "parts": [{'text': combined_prompt}]}]
        
        # Handle prefill
        if kwargs.get('prefill'):
            prefill_text = self._safe_strip_prefill(kwargs['prefill'])
            message_content.append({"role": "model", "parts": [{'text': prefill_text}]})
        
        # Return both system prompt and messages for Gemini API
        return {
            'system_instruction': system_prompt,
            'contents': message_content
        }
    
    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        return response.text if hasattr(response, 'text') else ''
    
    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from provider-specific response."""
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, 'prompt_token_count', None)
            completion_tokens = getattr(usage, 'candidates_token_count', None)
            
            return {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': (prompt_tokens or 0) + (completion_tokens or 0) if prompt_tokens and completion_tokens else None
            }
        return None
    
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        # Get the model with system instruction
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=messages['system_instruction']
        )
        
        generation_config = genai.GenerationConfig(
            max_output_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature'),
        )
        
        return model.generate_content(
            contents=messages['contents'],
            generation_config=generation_config,
            safety_settings=kwargs.get('gemini_safety_settings'),
        )
    
    def list_models(self) -> List[str]:
        """List available Gemini models."""
        logger.info("[Gemini] Fetching available models from Gemini API")
        try:
            # List models using the state genai module
            models = genai.list_models()
            # Filter for generateContent models
            gemini_models = [
                model.name.replace('models/', '') for model in models 
                if 'gemini' in model.name.lower() and 'generateContent' in model.supported_generation_methods
            ]
            logger.info(f"[Gemini] Found {len(gemini_models)} models")
            return sorted(gemini_models)
        except Exception as e:
            logger.error(f"[Gemini] Failed to fetch models from API: {str(e)}")
            # Use base class fallback models
            return super().list_models()