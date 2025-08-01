import asyncio
import base64
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import anthropic

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


class ClaudeAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models with full feature parity."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0

    def _initialize_client(self) -> anthropic.Anthropic:
        return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        supported_models = ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 
                           'claude-3.5-sonnet', 'claude-3.5-haiku']
        return any(model in self.model_name for model in supported_models)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call to Claude and return ChatResult."""
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Claude format with multi-modal support
        claude_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert content to Claude format
            content_blocks = self._convert_content_to_blocks(content)
            claude_messages.append({"role": role, "content": content_blocks})
        
        # Build system blocks with caching
        system_blocks = []
        if system_prompt:
            system_blocks.append(
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        
        # Convert tools to Claude format if provided
        tools = kwargs.pop('tools', None)
        claude_tools = None
        if tools and self.supports_tools():
            claude_tools = self._convert_tools_to_claude_format(tools)

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "top_p"])
        
        # Add tools if provided
        if claude_tools:
            api_params["tools"] = claude_tools

        # Make API call with retry logic
        response = self._make_api_call_with_retry(
            model=self.model_name,
            system=system_blocks,
            messages=claude_messages,
            **api_params,
        )

        # Process response and handle tool calls
        text = ""
        tool_outputs = []
        
        if response.content:
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    text += content_block.text
                elif hasattr(content_block, "type") and content_block.type == "tool_use":
                    # Handle tool calls
                    tool_output = self._process_tool_call(content_block)
                    if tool_output:
                        tool_outputs.append(tool_output)

        # Use base method to create token usage
        token_usage = self._create_token_usage(
            response, 
            input_field="input_tokens",
            output_field="output_tokens"
        )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None,
        )
    
    def _convert_tools_to_claude_format(self, tools: list) -> list[dict]:
        """Convert tools to Claude API format."""
        claude_tools = []
        
        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value
            
            if tool_type == "web_search" or tool_type == "web_search_preview":
                # Define web search tool for Claude
                claude_tools.append({
                    "name": "web_search",
                    "description": "Search the web for information",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                })
            elif tool_type == "image_generation":
                # Define image generation tool
                claude_tools.append({
                    "name": "generate_image",
                    "description": "Generate an image based on a text prompt",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The image generation prompt"
                            },
                            "size": {
                                "type": "string",
                                "description": "Image size",
                                "enum": ["1024x1024", "512x512", "256x256"],
                                "default": "1024x1024"
                            }
                        },
                        "required": ["prompt"]
                    }
                })
        
        return claude_tools
    
    def _process_tool_call(self, tool_use_block: Any) -> ToolOutput | None:
        """Process a tool call from Claude response."""
        if not hasattr(tool_use_block, "name") or not hasattr(tool_use_block, "input"):
            return None
            
        if tool_use_block.name == "web_search":
            query = tool_use_block.input.get("query", "")
            # Note: This returns placeholder data. In production, you would
            # execute the actual web search and return real results
            return ToolOutput(
                type=ToolType.WEB_SEARCH,
                result=[
                    WebSearchResult(
                        url=f"https://example.com/search?q={query}",
                        title=f"Search results for: {query}",
                        snippet=f"Placeholder search results for query: {query}",
                        score=1.0
                    )
                ],
                raw_response=tool_use_block
            )
        elif tool_use_block.name == "generate_image":
            prompt = tool_use_block.input.get("prompt", "")
            size = tool_use_block.input.get("size", "1024x1024")
            width, height = map(int, size.split("x"))
            # Note: This is a placeholder. Actual image generation would
            # require integration with an image generation service
            return ToolOutput(
                type=ToolType.IMAGE_GENERATION,
                result=ImageGenerationResult(
                    image_data="",  # Would be filled by actual generation
                    format="png",
                    width=width,
                    height=height
                ),
                raw_response=tool_use_block
            )
        return None
    
    def _convert_content_to_blocks(self, content: str | list | dict) -> list[dict]:
        """Convert message content to Claude content blocks."""
        # Handle simple string content
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        
        # Handle list of content items (multi-modal)
        if isinstance(content, list):
            blocks = []
            for item in content:
                if isinstance(item, str):
                    blocks.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        blocks.append({"type": "text", "text": item.get("text", "")})
                    elif item.get("type") == "image":
                        # Handle image content
                        image_block = self._process_image_content(item)
                        if image_block:
                            blocks.append(image_block)
            return blocks
        
        # Handle dict content (structured format)
        if isinstance(content, dict):
            if content.get("type") == "text":
                return [{"type": "text", "text": content.get("text", "")}]
            elif content.get("type") == "image":
                image_block = self._process_image_content(content)
                return [image_block] if image_block else [{"type": "text", "text": ""}]
        
        # Default case
        return [{"type": "text", "text": str(content)}]
    
    def _process_image_content(self, image_item: dict) -> dict | None:
        """Process image content for Claude API."""
        try:
            # Check for image URL
            if "url" in image_item:
                url = image_item["url"]
                if url.startswith("data:image"):
                    # Handle data URL
                    header, data = url.split(",", 1)
                    media_type = header.split(":")[1].split(";")[0]
                    return {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data
                        }
                    }
                else:
                    # For remote URLs, we'd need to download the image
                    logger.warning(f"Remote image URLs not yet supported: {url}")
                    return None
            
            # Check for base64 data
            elif "data" in image_item:
                media_type = image_item.get("media_type", "image/png")
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_item["data"]
                    }
                }
            
            # Check for raw bytes
            elif "bytes" in image_item:
                media_type = image_item.get("media_type", "image/png")
                data = base64.b64encode(image_item["bytes"]).decode('utf-8')
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to process image content: {e}")
        
        return None
    
    def _make_api_call_with_retry(self, **kwargs) -> Any:
        """Make API call with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Try to make the API call
                return self.client.messages.create(**kwargs)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(delay)
                        continue
                
                # Check if it's a content policy violation
                if "content_policy" in error_msg.lower():
                    logger.warning(f"Content policy violation: {error_msg}")
                    # Return empty response instead of failing
                    return self._create_empty_response("Content was blocked by content policy.")
                
                # For other errors, log and re-raise
                logger.error(f"Claude API error: {error_msg}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                    
                raise
        
        # If we've exhausted all retries, raise the last exception
        raise last_exception
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error",
            "overloaded"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for content policy violations."""
        # Create a mock response object that mimics the Claude response structure
        class MockResponse:
            def __init__(self, text):
                self.content = [MockContent(text)]
                self.usage = MockUsage()
                self.model = ""
                self.id = ""
                self.type = "message"
                self.role = "assistant"
        
        class MockContent:
            def __init__(self, text):
                self.text = text
                self.type = "text"
        
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
        
        return await self._make_api_call_async(messages, **kwargs)
    
    async def _make_api_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make async API call to Claude and return ChatResult."""
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Claude format with multi-modal support
        claude_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert content to Claude format
            content_blocks = self._convert_content_to_blocks(content)
            claude_messages.append({"role": role, "content": content_blocks})
        
        # Build system blocks with caching
        system_blocks = []
        if system_prompt:
            system_blocks.append(
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        
        # Convert tools to Claude format if provided
        tools = kwargs.pop('tools', None)
        claude_tools = None
        if tools and self.supports_tools():
            claude_tools = self._convert_tools_to_claude_format(tools)

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "top_p"])
        
        # Add tools if provided
        if claude_tools:
            api_params["tools"] = claude_tools

        # Make API call with retry logic
        response = await self._make_api_call_with_retry_async(
            model=self.model_name,
            system=system_blocks,
            messages=claude_messages,
            **api_params,
        )

        # Process response and handle tool calls
        text = ""
        tool_outputs = []
        
        if response.content:
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    text += content_block.text
                elif hasattr(content_block, "type") and content_block.type == "tool_use":
                    # Handle tool calls
                    tool_output = self._process_tool_call(content_block)
                    if tool_output:
                        tool_outputs.append(tool_output)

        # Use base method to create token usage
        token_usage = self._create_token_usage(
            response, 
            input_field="input_tokens",
            output_field="output_tokens"
        )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None,
        )
    
    async def _make_api_call_with_retry_async(self, **kwargs) -> Any:
        """Make async API call with exponential backoff retry logic."""
        last_exception = None
        
        # Create async client for async calls
        async_client = anthropic.AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
        
        for attempt in range(self.max_retries):
            try:
                # Try to make the API call
                return await async_client.messages.create(**kwargs)
                
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
                
                # Check if it's a content policy violation
                if "content_policy" in error_msg.lower():
                    logger.warning(f"Content policy violation: {error_msg}")
                    # Return empty response instead of failing
                    return self._create_empty_response("Content was blocked by content policy.")
                
                # For other errors, log and re-raise
                logger.error(f"Claude API error: {error_msg}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                    
                raise
        
        # If we've exhausted all retries, raise the last exception
        raise last_exception
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Claude format
        claude_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert content to Claude format
            content_blocks = self._convert_content_to_blocks(content)
            claude_messages.append({"role": role, "content": content_blocks})
        
        # Build system blocks with caching
        system_blocks = []
        if system_prompt:
            system_blocks.append(
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "top_p"])
        
        # Create async client for streaming
        async_client = anthropic.AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
        
        # Make streaming API call with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async with async_client.messages.stream(
                    model=self.model_name,
                    system=system_blocks,
                    messages=claude_messages,
                    **api_params,
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
                break  # Success, exit retry loop
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Streaming failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                raise
    
    async def get_available_models(self) -> list[str]:
        """Get available Anthropic Claude models."""
        try:
            # Create async client for model listing
            async_client = anthropic.AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
            models_response = await async_client.models.list(limit=50)
            
            model_ids = []
            for model in models_response.data:
                model_ids.append(model.id)
            
            model_ids.sort(reverse=True)
            return model_ids
            
        except Exception as e:
            logger.warning(f"Failed to fetch Anthropic models dynamically: {e}")
            # Return default models as fallback
            return [
                "claude-3.5-sonnet-20241022",
                "claude-3.5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]