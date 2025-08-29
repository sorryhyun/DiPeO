"""Async Claude adapter implementation."""

import asyncio
import base64
import logging
from collections.abc import AsyncIterator
from typing import Any

import anthropic

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


class ClaudeAsyncAdapter(BaseStreamingLLMAdapter, AsyncRetryMixin):
    """Async adapter for Anthropic Claude models."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        BaseStreamingLLMAdapter.__init__(self, model_name, api_key, base_url)
        AsyncRetryMixin.__init__(self)
    
    def _initialize_client(self) -> Any:
        """Initialize sync client (required by base class but not used)."""
        return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Sync API call (required by base class but not used)."""
        # This async adapter doesn't support sync calls
        raise NotImplementedError("ClaudeAsyncAdapter only supports async operations")
    
    async def _initialize_async_client(self) -> anthropic.AsyncAnthropic:
        """Initialize the async Anthropic client."""
        return anthropic.AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        """Check if this model supports tools."""
        supported_models = ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 
                           'claude-3.5-sonnet', 'claude-3.5-haiku']
        return any(model in self.model_name for model in supported_models)
    
    def _convert_tools_to_claude_format(self, tools: list) -> list[dict]:
        """Convert tools to Claude API format."""
        claude_tools = []
        
        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value
            
            if tool_type == "web_search" or tool_type == "web_search_preview":
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
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        
        if isinstance(content, list):
            blocks = []
            for item in content:
                if isinstance(item, str):
                    blocks.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        blocks.append({"type": "text", "text": item.get("text", "")})
                    elif item.get("type") == "image":
                        image_block = self._process_image_content(item)
                        if image_block:
                            blocks.append(image_block)
            return blocks
        
        if isinstance(content, dict):
            if content.get("type") == "text":
                return [{"type": "text", "text": content.get("text", "")}]
            elif content.get("type") == "image":
                image_block = self._process_image_content(content)
                return [image_block] if image_block else [{"type": "text", "text": ""}]
        
        return [{"type": "text", "text": str(content)}]
    
    def _process_image_content(self, image_item: dict) -> dict | None:
        """Process image content for Claude API."""
        try:
            if "url" in image_item:
                url = image_item["url"]
                if url.startswith("data:image"):
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
                    logger.warning(f"Remote image URLs not yet supported: {url}")
                    return None
            
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
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for content policy violations."""
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
    
    async def _make_api_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make async API call to Claude."""
        # Extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Claude format
        claude_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
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
        
        # Extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "top_p"])
        
        # Add tools if provided
        if claude_tools:
            api_params["tools"] = claude_tools
        
        # Get async client
        client = await self.get_async_client()
        
        # Make API call with retry logic
        async def make_call():
            return await client.messages.create(
                model=self.model_name,
                system=system_blocks,
                messages=claude_messages,
                **api_params,
            )
        
        # Handle content policy violations gracefully
        def handle_content_policy(e):
            error_msg = str(e)
            if "content_policy" in error_msg.lower():
                logger.warning(f"Content policy violation: {error_msg}")
                return self._create_empty_response("Content was blocked by content policy.")
            raise e
        
        try:
            response = await self._retry_with_backoff(
                make_call,
                on_empty_response=self._create_empty_response,
                error_message_prefix="Claude API"
            )
        except Exception as e:
            response = handle_content_policy(e)
        
        # Process response and handle tool calls
        text = ""
        tool_outputs = []
        
        if response.content:
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    text += content_block.text
                elif hasattr(content_block, "type") and content_block.type == "tool_use":
                    tool_output = self._process_tool_call(content_block)
                    if tool_output:
                        tool_outputs.append(tool_output)
        
        # Create token usage
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
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        # Extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Claude format
        claude_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
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
        
        # Extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature", "top_p"])
        
        # Get async client
        client = await self.get_async_client()
        
        # Make streaming API call with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async with client.messages.stream(
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
            client = await self.get_async_client()
            models_response = await client.models.list(limit=50)
            
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
    
    async def get_async_client(self) -> anthropic.AsyncAnthropic:
        """Get or create async client with thread-safe initialization."""
        if self._async_client is None:
            if self._client_lock is None:
                self._client_lock = asyncio.Lock()
            
            async with self._client_lock:
                if self._async_client is None:
                    self._async_client = await self._initialize_async_client()
        
        return self._async_client