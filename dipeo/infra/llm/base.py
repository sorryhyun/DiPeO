"""Base adapter for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any

from dipeo.models import ChatResult, LLMRequestOptions, TokenUsage


class BaseLLMAdapter(ABC):
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        raise NotImplementedError

    def chat(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        if messages is None:
            messages = []
        
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.tools and self.supports_tools():
                kwargs['tools'] = options.tools
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        return self._make_api_call(messages, **kwargs)
    
    def supports_tools(self) -> bool:
        return False
    
    def supports_response_api(self) -> bool:
        return False
    
    def _extract_system_and_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, str]]]:
        system_prompt = ""
        processed_messages = []
        
        if messages is None:
            return system_prompt, processed_messages
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            else:
                processed_messages.append({"role": role, "content": content})
        
        return system_prompt, processed_messages
    
    def _extract_api_params(self, kwargs: dict, allowed_params: list[str]) -> dict:
        return {
            k: v for k, v in kwargs.items() 
            if k in allowed_params and v is not None
        }
    
    def _create_token_usage(
        self, 
        response: Any,
        input_field: str | list[str],
        output_field: str | list[str],
        usage_attr: str = "usage"
    ) -> TokenUsage | None:
        usage_obj = getattr(response, usage_attr, None)
        if not usage_obj:
            return None
        
        input_fields = [input_field] if isinstance(input_field, str) else input_field
        output_fields = [output_field] if isinstance(output_field, str) else output_field
        
        input_tokens = None
        for field in input_fields:
            input_tokens = getattr(usage_obj, field, None)
            if input_tokens is not None:
                break
        
        output_tokens = None
        for field in output_fields:
            output_tokens = getattr(usage_obj, field, None)
            if output_tokens is not None:
                break
        
        if input_tokens is None and output_tokens is None:
            return None
        
        total = None
        if input_tokens is not None and output_tokens is not None:
            total = input_tokens + output_tokens
        
        return TokenUsage(
            input=input_tokens or 0,
            output=output_tokens or 0,
            total=total
        )