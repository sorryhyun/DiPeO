"""Refactored OpenAI adapter using centralized base logic."""

import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

from dipeo.models import (
    ImageGenerationResult,
    ToolConfig,
    ToolOutput,
    ToolType,
    WebSearchResult,
)
from dipeo.core.exceptions import LLMAPIError, LLMRateLimitError

from ..base_refactored import BaseLLMAdapter
from ..tool_converter import ToolConverter

logger = logging.getLogger(__name__)


class ChatGPTAdapter(BaseLLMAdapter):
    """Refactored OpenAI adapter with minimal provider-specific logic."""
    
    def _initialize_sync_client(self) -> OpenAI:
        """Initialize OpenAI sync client"""
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def _initialize_async_client(self) -> AsyncOpenAI:
        """Initialize OpenAI async client"""
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
    
    async def _make_provider_call_async(
        self, 
        messages: List[Dict[str, str]], 
        **provider_params
    ) -> Any:
        """Make OpenAI-specific API call (async)"""
        # Convert messages to OpenAI format
        input_messages = self._prepare_messages(messages)
        
        # Build create params
        create_params = {
            "model": provider_params.get('model', self.model_name),
            "input": input_messages,
        }
        
        # Add optional params
        if 'temperature' in provider_params:
            create_params['temperature'] = provider_params['temperature']
        
        # Add tools if present
        if 'tools' in provider_params:
            create_params['tools'] = provider_params['tools']
            logger.debug(f"Using tools with responses API: {provider_params['tools']}")
        
        # Make the API call
        return await self.async_client.responses.create(**create_params)
    
    def _make_provider_call_sync(
        self, 
        messages: List[Dict[str, str]], 
        **provider_params
    ) -> Any:
        """Make OpenAI-specific API call (sync)"""
        # Convert messages to OpenAI format
        input_messages = self._prepare_messages(messages)
        
        # Build create params
        create_params = {
            "model": provider_params.get('model', self.model_name),
            "input": input_messages,
        }
        
        # Add optional params
        if 'temperature' in provider_params:
            create_params['temperature'] = provider_params['temperature']
        
        # Add tools if present
        if 'tools' in provider_params:
            create_params['tools'] = provider_params['tools']
            logger.debug(f"Using tools with responses API: {provider_params['tools']}")
        
        # Make the API call
        return self.sync_client.responses.create(**create_params)
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert messages to OpenAI responses API format"""
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        input_messages = []
        
        # Add system prompt as developer role
        if system_prompt:
            input_messages.append({"role": "developer", "content": system_prompt})
        
        # Add other messages
        for msg in processed_messages:
            input_messages.append({"role": msg["role"], "content": msg["content"]})
        
        return input_messages
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract text from OpenAI response"""
        return getattr(response, 'output_text', '')
    
    def _extract_tool_calls(self, response: Any) -> Optional[List[ToolOutput]]:
        """Extract tool calls from OpenAI response"""
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
                        type=ToolType.web_search,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    # Handle image generation result
                    tool_outputs.append(ToolOutput(
                        type=ToolType.image_generation,
                        result=ImageGenerationResult(
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        return tool_outputs if tool_outputs else None
    
    def _get_token_usage_fields(self) -> Dict[str, Any]:
        """Get OpenAI-specific token usage field names"""
        return {
            'input_fields': ['input_tokens'],
            'output_fields': ['output_tokens'],
            'usage_attr': 'usage'
        }
    
    def supports_tools(self) -> bool:
        """Check if model supports tools"""
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_format(self) -> bool:
        """Check if model supports response format"""
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name
    
    def _get_allowed_params(self) -> List[str]:
        """Get allowed OpenAI parameters"""
        # Response API only supports temperature
        return ['temperature']
    
    def _convert_tools_for_provider(self, tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI format"""
        # For responses API, we use a simplified format
        api_tools = []
        
        for tool in tools:
            if not tool.enabled:
                continue
            
            if tool.type == ToolType.web_search_preview:
                api_tools.append({"type": "web_search_preview"})
            elif tool.type == ToolType.image_generation:
                api_tools.append({"type": "image_generation"})
            elif tool.type in [ToolType.voice, ToolType.speech_to_text, ToolType.text_to_speech]:
                logger.debug(f"{tool.type} requested but not supported in responses API")
        
        return api_tools
    
    def _map_provider_error(self, error: Exception) -> Exception:
        """Map OpenAI errors to domain exceptions"""
        error_str = str(error).lower()
        
        # Rate limit errors
        if "rate_limit" in error_str or "429" in error_str:
            return LLMRateLimitError(f"OpenAI rate limit exceeded: {error}")
        
        # API errors
        if any(keyword in error_str for keyword in ["timeout", "connection", "unavailable"]):
            return LLMAPIError(f"OpenAI API error: {error}")
        
        # Return original error if no mapping
        return error