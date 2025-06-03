from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Union
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChatResult:
    """Unified result type for all LLM adapters."""
    text: str
    usage: Optional[Any] = None  # Provider-specific usage object
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_response: Optional[Any] = None  # Original provider response
    
    @property
    def has_usage(self) -> bool:
        """Check if usage information is available."""
        return self.usage is not None or any([
            self.prompt_tokens, self.completion_tokens, self.total_tokens
        ])


class BaseAdapter(ABC):
    """Base interface for LLM adapters with common functionality."""
    
    # Provider-specific model fallbacks
    FALLBACK_MODELS: Dict[str, List[str]] = {
        'claude': [
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229',
            'claude-3-opus-20240229',
            'claude-3-5-sonnet-20241022',
            'claude-3-5-sonnet-20240620'
        ],
        'openai': [
            'gpt-4.1-nano',
            'gpt-3.5-turbo',
            'gpt-4',
            'gpt-4-turbo-preview',
            'gpt-4o',
            'gpt-4o-mini'
        ],
        'gemini': [
            'gemini-1.5-flash-002',
            'gemini-1.5-flash-8b',
            'gemini-1.5-pro-002',
            'gemini-2.0-flash-exp'
        ],
        'grok': [
            'grok-beta',
            'grok-vision-beta'
        ]
    }
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""
        raise NotImplementedError
    
    @abstractmethod
    def _build_messages(self, system_prompt: str, cacheable_prompt: str = '', 
                       user_prompt: str = '', citation_target: str = '', 
                       **kwargs) -> Union[List[Dict], str]:
        """Build provider-specific message format."""
        raise NotImplementedError
    
    @abstractmethod
    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        raise NotImplementedError
    
    @abstractmethod
    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from provider-specific response."""
        raise NotImplementedError
    
    @abstractmethod
    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        raise NotImplementedError
    
    def _safe_strip_prefill(self, prefill: str) -> str:
        """Safely strip whitespace from prefill text."""
        return prefill.rstrip().rstrip('\n') if prefill else ''
    
    def _combine_prompts(self, cacheable_prompt: str = '', user_prompt: str = '') -> str:
        """Combine cacheable and user prompts with proper spacing."""
        parts = [p for p in [cacheable_prompt, user_prompt] if p]
        return '\n\n'.join(parts)
    
    def _build_prefill_message(self, prefill: str, role: str = 'assistant') -> Dict[str, str]:
        """Build a prefill message with proper formatting."""
        return {
            'role': role,
            'content': self._safe_strip_prefill(prefill)
        }
    
    def chat(self, system_prompt: str, cacheable_prompt: str = '',
             user_prompt: str = '', citation_target: str = '', **kwargs) -> ChatResult:
        """
        Make a chat completion call with unified error handling.
        
        Subclasses should override _build_messages and _extract_* methods
        instead of overriding this method directly.
        """
        try:
            # Build provider-specific messages
            messages = self._build_messages(
                system_prompt=system_prompt,
                cacheable_prompt=cacheable_prompt,
                user_prompt=user_prompt,
                citation_target=citation_target,
                **kwargs
            )
            
            # Make the API call (pass system_prompt in kwargs for adapters that need it)
            api_kwargs = {**kwargs, 'system_prompt': system_prompt}
            response = self._make_api_call(messages, **api_kwargs)
            print(f"input\n\n{messages}")
            print(f"output\n\n{response}")
            # Extract results
            text = self._extract_text_from_response(response, **kwargs)
            usage_dict = self._extract_usage_from_response(response)
            return ChatResult(
                text=text,
                usage=response if hasattr(response, 'usage') else None,
                prompt_tokens=usage_dict.get('prompt_tokens') if usage_dict else None,
                completion_tokens=usage_dict.get('completion_tokens') if usage_dict else None,
                total_tokens=usage_dict.get('total_tokens') if usage_dict else None,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"LLM call failed for {self.__class__.__name__}: {str(e)}")
            return ChatResult(text='', usage=None)
    
    def list_models(self) -> List[str]:
        """
        List available models for this provider.
        
        Default implementation returns fallback models.
        Subclasses should override to add API-based model listing.
        """
        provider_name = self.__class__.__name__.replace('Adapter', '').lower()
        logger.info(f"[{provider_name}] Returning fallback models")
        return self.FALLBACK_MODELS.get(provider_name, [])
    
    def supports_tools(self) -> bool:
        """Check if this adapter supports tool/function calling."""
        return False
    
    def supports_citations(self) -> bool:
        """Check if this adapter supports citations."""
        return False
    
    def get_token_limits(self) -> Dict[str, int]:
        """Get token limits for the current model."""
        # Subclasses can override with model-specific limits
        return {
            'max_input_tokens': 100000,
            'max_output_tokens': 4096,
            'max_total_tokens': 104096
        }