"""Refactored base adapter for LLM providers with centralized common logic."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TypeVar
from functools import wraps

from dipeo.models import (
    ChatResult, LLMRequestOptions, TokenUsage, Message,
    ToolConfig, ToolOutput
)
from dipeo.core.exceptions import LLMAPIError, LLMRateLimitError
from .retry_manager import RetryManager, RetryStrategy
from .tool_converter import ToolConverter

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseLLMAdapter(ABC):
    """
    Refactored base adapter that handles all common LLM logic.
    Adapters only need to implement provider-specific methods.
    """
    
    def __init__(
        self, 
        model_name: str, 
        api_key: str, 
        base_url: Optional[str] = None,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.retry_strategy = retry_strategy or RetryManager.DEFAULT_STRATEGY
        
        # Initialize clients
        self._sync_client = None
        self._async_client = None
    
    @property
    def sync_client(self) -> Any:
        """Lazy initialization of sync client"""
        if self._sync_client is None:
            self._sync_client = self._initialize_sync_client()
        return self._sync_client
    
    @property
    def async_client(self) -> Any:
        """Lazy initialization of async client"""
        if self._async_client is None:
            self._async_client = self._initialize_async_client()
        return self._async_client
    
    @abstractmethod
    def _initialize_sync_client(self) -> Any:
        """Initialize provider-specific sync client"""
        pass
    
    @abstractmethod
    def _initialize_async_client(self) -> Any:
        """Initialize provider-specific async client"""
        pass
    
    @abstractmethod
    async def _make_provider_call_async(
        self, 
        messages: List[Dict[str, str]], 
        **provider_params
    ) -> Any:
        """Make provider-specific API call (async)"""
        pass
    
    @abstractmethod
    def _make_provider_call_sync(
        self, 
        messages: List[Dict[str, str]], 
        **provider_params
    ) -> Any:
        """Make provider-specific API call (sync)"""
        pass
    
    @abstractmethod
    def _extract_response_text(self, response: Any) -> str:
        """Extract text from provider-specific response"""
        pass
    
    @abstractmethod
    def _extract_tool_calls(self, response: Any) -> Optional[List[ToolOutput]]:
        """Extract tool calls from provider-specific response"""
        pass
    
    @abstractmethod
    def _get_token_usage_fields(self) -> Dict[str, Union[str, List[str]]]:
        """Get provider-specific token usage field names"""
        # Return format: {
        #     'input_fields': ['input_tokens', 'prompt_tokens'],
        #     'output_fields': ['output_tokens', 'completion_tokens'],
        #     'usage_attr': 'usage'
        # }
        pass
    
    async def chat_async(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> ChatResult:
        """Async chat with retry logic and common processing"""
        # Extract and validate parameters
        params = self._prepare_request_params(messages, kwargs)
        
        # Execute with retry
        @RetryManager.with_retry(
            strategy=self.retry_strategy,
            retryable_errors=(LLMAPIError, LLMRateLimitError)
        )
        async def _execute():
            try:
                response = await self._make_provider_call_async(**params)
                return self._process_response(response)
            except Exception as e:
                raise self._map_provider_error(e)
        
        return await _execute()
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> ChatResult:
        """Sync chat with retry logic and common processing"""
        # Extract and validate parameters
        params = self._prepare_request_params(messages, kwargs)
        
        # Execute with retry
        @RetryManager.with_retry(
            strategy=self.retry_strategy,
            retryable_errors=(LLMAPIError, LLMRateLimitError)
        )
        def _execute():
            try:
                response = self._make_provider_call_sync(**params)
                return self._process_response(response)
            except Exception as e:
                raise self._map_provider_error(e)
        
        return _execute()
    
    def _prepare_request_params(
        self, 
        messages: List[Dict[str, str]], 
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare and validate request parameters"""
        # Ensure messages is not None
        if messages is None:
            messages = []
        
        # Extract options from kwargs
        options = kwargs.get('options')
        
        # Build base parameters
        params = {
            'messages': messages,
            'model': self.model_name
        }
        
        # Handle LLMRequestOptions
        if isinstance(options, LLMRequestOptions):
            # Temperature
            if options.temperature is not None:
                params['temperature'] = options.temperature
            
            # Max tokens
            if options.max_tokens is not None:
                params['max_tokens'] = options.max_tokens
            
            # Top P
            if options.top_p is not None:
                params['top_p'] = options.top_p
            
            # Response format
            if options.response_format is not None:
                params['response_format'] = options.response_format
            
            # Tools
            if options.tools and self.supports_tools():
                normalized_tools = ToolConverter.normalize_tools(options.tools)
                params['tools'] = self._convert_tools_for_provider(normalized_tools)
        
        # Extract provider-specific parameters
        allowed_params = self._get_allowed_params()
        for key, value in kwargs.items():
            if key in allowed_params and key not in params and value is not None:
                params[key] = value
        
        return params
    
    def _process_response(self, response: Any) -> ChatResult:
        """Process provider response into ChatResult"""
        # Extract text
        text = self._extract_response_text(response)
        
        # Extract token usage
        usage_fields = self._get_token_usage_fields()
        token_usage = self._create_token_usage(
            response,
            usage_fields['input_fields'],
            usage_fields['output_fields'],
            usage_fields.get('usage_attr', 'usage')
        )
        
        # Extract tool outputs
        tool_outputs = self._extract_tool_calls(response)
        
        # Build result
        result = ChatResult(
            text=text,
            token_usage=token_usage
        )
        
        # Add tool outputs if present
        if tool_outputs:
            result.tool_outputs = tool_outputs
        
        return result
    
    def _create_token_usage(
        self,
        response: Any,
        input_fields: Union[str, List[str]],
        output_fields: Union[str, List[str]],
        usage_attr: str = "usage"
    ) -> Optional[TokenUsage]:
        """Create TokenUsage from response"""
        usage_obj = getattr(response, usage_attr, None)
        if not usage_obj:
            return None
        
        # Normalize to lists
        input_fields = [input_fields] if isinstance(input_fields, str) else input_fields
        output_fields = [output_fields] if isinstance(output_fields, str) else output_fields
        
        # Extract input tokens
        input_tokens = None
        for field in input_fields:
            input_tokens = getattr(usage_obj, field, None)
            if input_tokens is not None:
                break
        
        # Extract output tokens
        output_tokens = None
        for field in output_fields:
            output_tokens = getattr(usage_obj, field, None)
            if output_tokens is not None:
                break
        
        if input_tokens is None and output_tokens is None:
            return None
        
        # Calculate total
        total = None
        if input_tokens is not None and output_tokens is not None:
            total = input_tokens + output_tokens
        
        return TokenUsage(
            input=input_tokens or 0,
            output=output_tokens or 0,
            total=total
        )
    
    def _extract_system_and_messages(
        self, 
        messages: List[Dict[str, str]]
    ) -> tuple[str, List[Dict[str, str]]]:
        """Extract system prompt and process messages"""
        system_prompt = ""
        processed_messages = []
        
        if not messages:
            return system_prompt, processed_messages
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            else:
                processed_messages.append({"role": role, "content": content})
        
        return system_prompt, processed_messages
    
    # Provider-specific configuration methods
    
    def supports_tools(self) -> bool:
        """Override to indicate tool support"""
        return False
    
    def supports_response_format(self) -> bool:
        """Override to indicate response format support"""
        return False
    
    def supports_vision(self) -> bool:
        """Override to indicate vision/image support"""
        return False
    
    @abstractmethod
    def _get_allowed_params(self) -> List[str]:
        """Get list of allowed provider-specific parameters"""
        pass
    
    @abstractmethod
    def _convert_tools_for_provider(self, tools: List[ToolConfig]) -> Any:
        """Convert normalized tools to provider-specific format"""
        pass
    
    @abstractmethod
    def _map_provider_error(self, error: Exception) -> Exception:
        """Map provider-specific errors to domain exceptions"""
        pass