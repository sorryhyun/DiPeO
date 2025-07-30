# openai_adapter.py

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, OpenAI

from dipeo.models import (
    ChatResult,
    ImageGenerationResult,
    LLMRequestOptions,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

from ..base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ChatGPTAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models with full feature parity."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        # Models that support tools including websearch via responses API
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name

    def _prepare_api_request(self, messages: list[dict[str, str]], **kwargs) -> tuple[list[dict], list[dict], dict]:
        """Prepare common API request parameters for both sync and async calls."""
        tools = kwargs.pop('tools', [])
        system_prompt_kwarg = kwargs.pop('system_prompt', None)

        # Guard against None or empty messages
        if not messages:
            logger.warning("No messages provided to OpenAI API call")
            return [], [], {}

        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Use system_prompt from kwargs if provided, otherwise use extracted one
        if system_prompt_kwarg:
            system_prompt = system_prompt_kwarg
        
        # Build input messages with response API format
        input_messages = []
        if system_prompt:
            # Response API uses developer instead of system
            input_messages.append({"role": "developer", "content": system_prompt})
        
        # Add other messages
        for msg in processed_messages:
            input_messages.append({"role": msg["role"], "content": msg["content"]})

        logger.debug(f"Input messages: {input_messages}")
        
        # Convert tools to API format
        api_tools = []
        if tools:
            for tool in tools:
                if tool.type == "web_search_preview" or (hasattr(tool.type, 'value') and tool.type.value == "web_search_preview"):
                    api_tools.append({"type": "web_search_preview"})
                elif tool.type == "image_generation" or (hasattr(tool.type, 'value') and tool.type.value == "image_generation"):
                    api_tools.append({"type": "image_generation"})
        
        if api_tools:
            logger.debug(f"API tools: {api_tools}")
        
        # Use base method to extract allowed parameters
        # Note: responses API doesn't support max_tokens parameter
        api_params = self._extract_api_params(kwargs, ["temperature"])
        
        return input_messages, api_tools, api_params
    
    def _process_api_response(self, response: Any) -> tuple[str, list[ToolOutput] | None, dict]:
        """Process API response to extract text, tool outputs, and token usage."""
        # Extract text output
        text = getattr(response, 'output_text', '')
        logger.debug(f"Output text: {text}")
        
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
                            width=1024,  # Default values, could be extracted from metadata
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        # Create token usage without logging
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )
        
        return text, tool_outputs if tool_outputs else None, token_usage
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        # Prepare request
        input_messages, api_tools, api_params = self._prepare_api_request(messages, **kwargs)
        
        if not input_messages:
            return ChatResult(text='', raw_response=None)
        
        # Make response API call with retry logic
        response = self._make_api_call_with_retry(
            input_messages=input_messages,
            api_tools=api_tools,
            api_params=api_params
        )
        
        # Process response
        text, tool_outputs, token_usage = self._process_api_response(response)
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs
        )
    
    def _make_api_call_with_retry(self, input_messages: list, api_tools: list, api_params: dict) -> Any:
        """Make API call with exponential backoff retry logic (sync version)."""
        # Run the async version in a new event loop for sync context
        return asyncio.run(self._make_api_call_with_retry_async(
            input_messages=input_messages,
            api_tools=api_tools,
            api_params=api_params,
            is_sync=True
        ))
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for error cases."""
        # Create a mock response object that mimics the OpenAI response structure
        class MockResponse:
            def __init__(self, text):
                self.output_text = text
                self.output = []
                self.usage = MockUsage()
                self.model = ""
                self.id = ""
        
        class MockUsage:
            def __init__(self):
                self.input_tokens = 0
                self.output_tokens = 0
        
        return MockResponse(message)
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async version of chat method."""
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
        
        # Prepare request
        input_messages, api_tools, api_params = self._prepare_api_request(messages, **kwargs)
        
        if not input_messages:
            return ChatResult(text='', raw_response=None)
        
        # Make response API call with retry logic
        response = await self._make_api_call_with_retry_async(
            input_messages=input_messages,
            api_tools=api_tools,
            api_params=api_params
        )
        
        # Process response
        text, tool_outputs, token_usage = self._process_api_response(response)
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs
        )
    
    
    async def _make_api_call_with_retry_async(self, input_messages: list, api_tools: list, api_params: dict, is_sync: bool = False) -> Any:
        """Make async API call with exponential backoff retry logic."""
        last_exception = None
        
        # Create appropriate client based on context
        if is_sync:
            client = self.client
        else:
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        for attempt in range(self.max_retries):
            try:
                # Build API call parameters
                create_params = {
                    "model": self.model_name,
                    "input": input_messages,
                    **api_params
                }
                
                # Add tools if they exist and are supported
                if api_tools and self.supports_tools():
                    create_params["tools"] = api_tools
                    logger.debug(f"Using tools with responses API: {api_tools}")
                
                # Try to make the API call
                if is_sync:
                    return client.responses.create(**create_params)
                else:
                    return await client.responses.create(**create_params)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                
                # Log error
                logger.error(f"OpenAI API error: {error_msg}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                    
                # For final attempt or non-retriable errors, return empty result
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts exhausted for OpenAI API")
                    return self._create_empty_response(f"API call failed after {self.max_retries} attempts")
        
        # If we've exhausted all retries, return empty response
        return self._create_empty_response("Failed to get response from OpenAI API")
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        # Note: OpenAI Response API doesn't support streaming in the same way
        # This is a simplified implementation that yields the full response
        result = await self.chat_async(messages, **kwargs)
        if result.text:
            yield result.text
