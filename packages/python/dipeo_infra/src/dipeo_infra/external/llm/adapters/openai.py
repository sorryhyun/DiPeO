# openai_adapter.py

import base64
from typing import Any

from dipeo_domain import ChatResult, TokenUsage, ToolOutput, ToolType, WebSearchResult, ImageGenerationResult
from openai import OpenAI

from ..base import BaseAdapter


class ChatGPTAdapter(BaseAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        """Check if this model supports tool usage."""
        # Only certain models support tools
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1-nano']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        """Check if this model supports the new response API."""
        # Response API is supported for specific models
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        # Check if we should use the response API
        tools = kwargs.pop('tools', None)
        if tools and self.supports_response_api() and self.supports_tools():
            return self._make_response_api_call(messages, tools, **kwargs)
        
        # Otherwise use the standard chat API
        return self._make_chat_api_call(messages, **kwargs)
    
    def _make_chat_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Standard chat completion API call."""
        # Map roles for OpenAI compatibility
        mapped_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # OpenAI uses "developer" role instead of "system" in newer models
            if role == "system" and "o1" in self.model_name:
                role = "developer"
            mapped_messages.append({"role": role, "content": msg.get("content", "")})

        # Extract allowed parameters
        allowed_params = ["temperature", "max_tokens", "n", "top_p"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        # Make API call
        params = {"model": self.model_name, "messages": mapped_messages, **api_params}
        response = self.client.chat.completions.create(**params)

        # Extract response data
        text = ""
        if response.choices:
            text = response.choices[0].message.content or ""

        # Extract usage
        prompt_tokens = None
        completion_tokens = None

        if hasattr(response, "usage") and response.usage:
            prompt_tokens = getattr(response.usage, "prompt_tokens", None)
            completion_tokens = getattr(response.usage, "completion_tokens", None)

        # Create TokenUsage if we have usage data
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            token_usage = TokenUsage(
                input=prompt_tokens or 0,
                output=completion_tokens or 0,
                total=(prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None and completion_tokens is not None
                else None,
            )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
        )
    
    def _make_response_api_call(self, messages: list[dict[str, str]], tools: list, **kwargs) -> ChatResult:
        """Use the new response API with tool support."""
        # Convert messages to response API format
        input_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                role = "developer"  # Response API uses developer instead of system
            input_messages.append({"role": role, "content": msg.get("content", "")})
        
        # Convert tools to API format
        api_tools = []
        for tool in tools:
            if tool.type == "web_search_preview" or (hasattr(tool.type, 'value') and tool.type.value == "web_search_preview"):
                api_tools.append({"type": "web_search_preview"})
            elif tool.type == "image_generation" or (hasattr(tool.type, 'value') and tool.type.value == "image_generation"):
                api_tools.append({"type": "image_generation"})
        
        # Make response API call
        try:
            response = self.client.responses.create(
                model=self.model_name,
                input=input_messages,
                tools=api_tools if api_tools else None,
                **{k: v for k, v in kwargs.items() if k in ["temperature", "max_tokens"] and v is not None}
            )
        except AttributeError:
            # Fallback to chat API if responses is not available
            return self._make_chat_api_call(messages, **kwargs)
        
        # Extract text output
        text = getattr(response, 'output_text', '')
        
        # Process tool outputs
        tool_outputs = []
        if hasattr(response, 'output') and response.output:
            for output in response.output:
                if output.type == 'web_search_call' and hasattr(output, 'result'):
                    # Parse web search results
                    search_results = []
                    for result in output.result:
                        search_results.append(WebSearchResult(
                            url=result.get('url', ''),
                            title=result.get('title', ''),
                            snippet=result.get('snippet', ''),
                            score=result.get('score')
                        ))
                    tool_outputs.append(ToolOutput(
                        type=ToolType.WEB_SEARCH_PREVIEW,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    # Handle image generation result
                    tool_outputs.append(ToolOutput(
                        type=ToolType.IMAGE_GENERATION,
                        result=ImageGenerationResult(
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,  # Default values, could be extracted from metadata
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        # Extract token usage if available
        token_usage = None
        if hasattr(response, 'usage'):
            token_usage = TokenUsage(
                input=getattr(response.usage, 'prompt_tokens', 0),
                output=getattr(response.usage, 'completion_tokens', 0),
                total=getattr(response.usage, 'total_tokens', 0)
            )
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None
        )

