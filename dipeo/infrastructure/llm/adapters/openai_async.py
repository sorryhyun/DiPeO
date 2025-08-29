"""Async OpenAI adapter implementation."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from dipeo.diagram_generated import (
    ChatResult,
    ImageGenerationResult,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

from .base_async import BaseStreamingLLMAdapter
from .mixins.retry import AsyncRetryMixin

logger = logging.getLogger(__name__)


class ExecutionPhase:
    """Execution phases for DiPeO workflows."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


class MemorySelectionOutput(BaseModel):
    """Structured output model for memory selection phase."""
    message_ids: list[str]


class OpenAIAsyncAdapter(BaseStreamingLLMAdapter, AsyncRetryMixin):
    """Async adapter for OpenAI GPT models."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        BaseStreamingLLMAdapter.__init__(self, model_name, api_key, base_url)
        AsyncRetryMixin.__init__(self)
    
    def _initialize_client(self) -> Any:
        """Initialize sync client (required by base class but not used)."""
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Sync API call (required by base class but not used)."""
        # This async adapter doesn't support sync calls
        raise NotImplementedError("OpenAIAsyncAdapter only supports async operations")
    
    async def _initialize_async_client(self) -> AsyncOpenAI:
        """Initialize the async OpenAI client."""
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        """Check if this model supports tools."""
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        """Check if this model supports the response API."""
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name
    
    def _is_temperature_unsupported_model(self) -> bool:
        """Check if the model doesn't support temperature parameter."""
        return 'gpt-5' in self.model_name
    
    def _prepare_api_request(self, messages: list[dict[str, str]], **kwargs) -> tuple[list[dict], list[dict], dict]:
        """Prepare common API request parameters."""
        execution_phase = kwargs.pop('execution_phase', ExecutionPhase.DEFAULT)
        tools = kwargs.pop('tools', [])
        text_format = kwargs.pop('text_format', None)

        if not messages:
            logger.warning("No messages provided to OpenAI API call")
            return [], [], {}

        input_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role in ["user", "assistant", "system", "developer"]:
                input_messages.append({"role": role, "content": content})
            else:
                logger.warning(f"Unknown role '{role}' in message, using 'user'")
                input_messages.append({"role": "user", "content": content})

        api_tools = []
        if tools:
            for tool in tools:
                if tool.type == "web_search_preview" or (hasattr(tool.type, 'value') and tool.type.value == "web_search_preview"):
                    api_tools.append({"type": "web_search_preview"})
                elif tool.type == "image_generation" or (hasattr(tool.type, 'value') and tool.type.value == "image_generation"):
                    api_tools.append({"type": "image_generation"})
        
        if api_tools:
            logger.debug(f"API tools: {api_tools}")
        
        allowed_params = []
        if not self._is_temperature_unsupported_model():
            allowed_params.append("temperature")
        api_params = self._extract_api_params(kwargs, allowed_params)
        
        # Handle memory selection phase with structured output
        if execution_phase == ExecutionPhase.MEMORY_SELECTION or execution_phase == "memory_selection":
            if not text_format:
                api_params["_pydantic_model"] = MemorySelectionOutput
                logger.debug("Using structured output for memory selection phase")
        
        # Handle explicitly provided text_format
        if text_format:
            if isinstance(text_format, type) and issubclass(text_format, BaseModel):
                api_params["_pydantic_model"] = text_format
            else:
                logger.warning(f"text_format must be a Pydantic BaseModel class, got {type(text_format)}")
        
        return input_messages, api_tools, api_params
    
    def _process_api_response(self, response: Any) -> tuple[str, list[ToolOutput] | None, dict]:
        """Process API response to extract text, tool outputs, and token usage."""
        import json
        
        # Handle structured output
        if hasattr(response, 'output_parsed'):
            parsed_output = response.output_parsed
            if parsed_output:
                if isinstance(parsed_output, MemorySelectionOutput):
                    text = json.dumps(parsed_output.message_ids)
                elif isinstance(parsed_output, BaseModel):
                    text = json.dumps(parsed_output.model_dump())
                else:
                    text = json.dumps(parsed_output)
            else:
                text = ''
        elif hasattr(response, 'parsed'):
            parsed_output = response.parsed
            if parsed_output:
                if isinstance(parsed_output, MemorySelectionOutput):
                    text = json.dumps(parsed_output.message_ids)
                elif isinstance(parsed_output, BaseModel):
                    text = json.dumps(parsed_output.model_dump())
                else:
                    text = json.dumps(parsed_output)
            else:
                text = ''
        else:
            text = getattr(response, 'output_text', '')

        # Process tool outputs
        tool_outputs = []
        if hasattr(response, 'output') and response.output:
            for output in response.output:
                if output.type == 'web_search_call' and hasattr(output, 'result'):
                    search_results = []
                    for result in output.result:
                        search_results.append(WebSearchResult(
                            url=result.get('url', ''),
                            title=result.get('title', ''),
                            snippet=result.get('snippet', ''),
                            score=result.get('score')
                        ))
                    tool_outputs.append(ToolOutput(
                        type=ToolType.WEB_SEARCH,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    tool_outputs.append(ToolOutput(
                        type=ToolType.IMAGE_GENERATION,
                        result=ImageGenerationResult(
                            image_data=output.result,
                            format='png',
                            width=1024,
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        # Create token usage
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )
        
        return text, tool_outputs if tool_outputs else None, token_usage
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for error cases."""
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
    
    async def _make_api_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make async API call to OpenAI."""
        # Prepare request
        input_messages, api_tools, api_params = self._prepare_api_request(messages, **kwargs)
        if not input_messages:
            return ChatResult(text='', raw_response=None)
        
        # Get async client
        client = await self.get_async_client()
        
        # Make API call with retry logic
        async def make_call():
            pydantic_model = api_params.pop('_pydantic_model', None)
            
            create_params = {
                "model": self.model_name,
                "input": input_messages,
                **api_params
            }
            
            if api_tools and self.supports_tools():
                create_params["tools"] = api_tools
                logger.debug(f"Using tools with responses API: {api_tools}")
            
            if pydantic_model:
                logger.debug(f"Using responses.parse() with Pydantic model: {pydantic_model.__name__}")
                create_params['text_format'] = pydantic_model
                return await client.responses.parse(**create_params)
            else:
                return await client.responses.create(**create_params)
        
        response = await self._retry_with_backoff(
            make_call,
            on_empty_response=self._create_empty_response,
            error_message_prefix="OpenAI API"
        )
        
        # Process response
        text, tool_outputs, token_usage = self._process_api_response(response)
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs
        )
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        # For now, just return the full response as a single chunk
        # Full streaming implementation would require additional API changes
        result = await self.chat_async(messages, **kwargs)
        if result.text:
            yield result.text
    
    async def get_available_models(self) -> list[str]:
        """Get available OpenAI models."""
        try:
            client = await self.get_async_client()
            models_response = await client.models.list()
            
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                if any(prefix in model_id for prefix in ["gpt-", "o1", "o3", "chatgpt"]):
                    chat_models.append(model_id)
            
            # Ensure gpt-5-nano-2025-08-07 is included
            if "gpt-5-nano-2025-08-07" not in chat_models:
                chat_models.append("gpt-5-nano-2025-08-07")
            
            chat_models.sort(reverse=True)
            return chat_models
            
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models dynamically: {e}")
            # Return default models as fallback
            return [
                "gpt-5-nano-2025-08-07",
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
    
    async def get_async_client(self) -> AsyncOpenAI:
        """Get or create async client with thread-safe initialization."""
        if self._async_client is None:
            if self._client_lock is None:
                self._client_lock = asyncio.Lock()
            
            async with self._client_lock:
                if self._async_client is None:
                    self._async_client = await self._initialize_async_client()
        
        return self._async_client