import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any
from enum import Enum

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from dipeo.diagram_generated import (
    ChatResult,
    ImageGenerationResult,
    LLMRequestOptions,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

from ..drivers.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ExecutionPhase(str, Enum):
    """Execution phases for DiPeO workflows."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


class MemorySelectionOutput(BaseModel):
    """Structured output model for memory selection phase."""
    message_ids: list[str]


class ChatGPTAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models with full feature parity."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0
        self._async_client = None
        self._client_lock = None

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name
    
    def _is_temperature_unsupported_model(self) -> bool:
        """Check if the model doesn't support temperature parameter."""
        return 'gpt-5' in self.model_name

    def _prepare_api_request(self, messages: list[dict[str, str]], **kwargs) -> tuple[list[dict], list[dict], dict]:
        """Prepare common API request parameters for both sync and async calls."""
        # Pop execution_phase early so it doesn't get passed to validation
        execution_phase = kwargs.pop('execution_phase', ExecutionPhase.DEFAULT)
        tools = kwargs.pop('tools', [])
        text_format = kwargs.pop('text_format', None)

        if not messages:
            logger.warning("No messages provided to OpenAI API call")
            return [], [], {}

        input_messages = []

        # Process messages and handle special roles
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # OpenAI's responses API accepts "developer" role for system messages
            # The "developer" role provides stronger instruction adherence than "system"
            # This is already handled by the infrastructure layer, but we validate it here
            if role in ["user", "assistant", "system", "developer"]:
                input_messages.append({"role": role, "content": content})
            else:
                # Fallback to "user" for unknown roles
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
            # Use structured output for memory selection to ensure valid JSON array
            if not text_format:  # Only set if not already provided
                api_params["_pydantic_model"] = MemorySelectionOutput
                logger.debug("Using structured output for memory selection phase")
        
        # Handle explicitly provided text_format
        if text_format:
            from pydantic import BaseModel
            
            if isinstance(text_format, type) and issubclass(text_format, BaseModel):
                api_params["_pydantic_model"] = text_format
            else:
                logger.warning(f"text_format must be a Pydantic BaseModel class, got {type(text_format)}")
        
        return input_messages, api_tools, api_params
    
    def _process_api_response(self, response: Any) -> tuple[str, list[ToolOutput] | None, dict]:
        """Process API response to extract text, tool outputs, and token usage."""
        if hasattr(response, 'output_parsed'):
            import json
            from pydantic import BaseModel
            
            parsed_output = response.output_parsed
            if parsed_output:
                if isinstance(parsed_output, MemorySelectionOutput):
                    # For memory selection, return just the message IDs as a JSON array
                    text = json.dumps(parsed_output.message_ids)
                elif isinstance(parsed_output, BaseModel):
                    text = json.dumps(parsed_output.model_dump())
                else:
                    text = json.dumps(parsed_output)
            else:
                text = ''
        elif hasattr(response, 'parsed'):
            import json
            from pydantic import BaseModel
            
            parsed_output = response.parsed
            if parsed_output:
                if isinstance(parsed_output, MemorySelectionOutput):
                    # For memory selection, return just the message IDs as a JSON array
                    text = json.dumps(parsed_output.message_ids)
                elif isinstance(parsed_output, BaseModel):
                    text = json.dumps(parsed_output.model_dump())
                else:
                    text = json.dumps(parsed_output)
            else:
                text = ''
        else:
            text = getattr(response, 'output_text', '')

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
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,
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
        # print(input_messages)
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
            # Initialize lock if needed (first time)
            if self._client_lock is None:
                self._client_lock = asyncio.Lock()
            
            # Use cached async client or create one
            async with self._client_lock:
                if self._async_client is None:
                    self._async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
                client = self._async_client
        
        for attempt in range(self.max_retries):
            try:
                # Check if we have a Pydantic model for structured output
                pydantic_model = api_params.pop('_pydantic_model', None)
                
                # Build API call parameters
                print(api_params)
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
                    if pydantic_model:
                        logger.debug(f"Using responses.parse() with Pydantic model: {pydantic_model.__name__}")
                        # For Pydantic models, pass the model class directly
                        create_params['text_format'] = pydantic_model
                        return client.responses.parse(**create_params)
                    else:
                        return client.responses.create(**create_params)
                else:
                    if pydantic_model:
                        logger.debug(f"Using responses.parse() with Pydantic model: {pydantic_model.__name__}")
                        # For Pydantic models, pass the model class directly
                        create_params['text_format'] = pydantic_model
                        return await client.responses.parse(**create_params)
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
        result = await self.chat_async(messages, **kwargs)
        if result.text:
            yield result.text
    
    async def get_available_models(self) -> list[str]:
        """Get available OpenAI models."""
        try:
            models_response = await asyncio.to_thread(self.client.models.list)
            
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                if any(prefix in model_id for prefix in ["gpt-", "o1", "o3", "chatgpt"]):
                    chat_models.append(model_id)
            
            # Ensure gpt-4.1-nano is included
            if "gpt-4.1-nano" not in chat_models:
                chat_models.append("gpt-4.1-nano")
            
            chat_models.sort(reverse=True)
            return chat_models
            
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models dynamically: {e}")
            # Return default models as fallback
            return [
                "gpt-4.1-nano",
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
