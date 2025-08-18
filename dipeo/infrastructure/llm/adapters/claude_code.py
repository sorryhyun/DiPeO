import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any
from contextlib import asynccontextmanager

from dipeo.diagram_generated import (
    ChatResult,
    LLMRequestOptions,
    TokenUsage,
)

from ...services.llm.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(BaseLLMAdapter):
    """Adapter for Claude Code SDK with streaming-first architecture."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0
        self._active_clients = {}  # Track active client contexts
        self._client_lock = asyncio.Lock()
        
    def _initialize_client(self) -> Any:
        # Claude Code SDK doesn't use a traditional client initialization
        # Client is created in async context manager
        return None
    
    def supports_tools(self) -> bool:
        # Claude Code SDK has different tool support patterns
        return False
    
    def supports_response_api(self) -> bool:
        return False
    
    @asynccontextmanager
    async def _create_claude_code_client(self, system_prompt: str | None = None, max_turns: int = 1):
        """Create Claude Code SDK client with async context manager."""
        try:
            from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        except ImportError as e:
            logger.error("claude-code-sdk not installed. Install with: pip install claude-code-sdk")
            raise ImportError("claude-code-sdk is required for Claude Code support") from e
        
        # Prepare options
        options_dict = {}
        if system_prompt:
            options_dict["system_prompt"] = system_prompt
        if max_turns:
            options_dict["max_turns"] = max_turns
            
        options = ClaudeCodeOptions(**options_dict)
        # Create and yield client
        async with ClaudeSDKClient(options=options) as client:
            yield client
    
    def _extract_system_prompt_and_options(self, messages: list[dict[str, str]], **kwargs) -> tuple[str, list[dict], dict]:
        """Extract system prompt and options from messages and kwargs."""
        system_prompt = ""
        user_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_messages.append(msg)
            # Note: Claude Code SDK handles conversation context internally
            
        # Extract Claude Code specific options
        claude_code_options = {
            "max_turns": kwargs.get("max_turns", 1),
        }
        
        return system_prompt, user_messages, claude_code_options
    
    async def _stream_response_to_text(self, client, query: str) -> tuple[str, TokenUsage | None]:
        """Stream response from Claude Code client and collect text."""
        full_text = ""
        input_tokens = 0
        output_tokens = 0
        
        try:
            # Send the query
            await client.query(query)
            
            # Stream and collect responses
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_text += block.text
                
                # Try to extract token usage if available
                if hasattr(message, 'usage'):
                    if hasattr(message.usage, 'input_tokens'):
                        input_tokens = message.usage.input_tokens
                    if hasattr(message.usage, 'output_tokens'):
                        output_tokens = message.usage.output_tokens
                        
        except Exception as e:
            logger.error(f"Error streaming Claude Code response: {e}")
            raise
        
        token_usage = None
        if input_tokens or output_tokens:
            token_usage = TokenUsage(
                input=input_tokens,
                output=output_tokens,
                total=input_tokens + output_tokens if input_tokens and output_tokens else None
            )
        
        return full_text, token_usage
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Synchronous wrapper for async Claude Code API calls."""
        return asyncio.run(self.chat_async(messages, **kwargs))
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async chat method for Claude Code SDK."""
        if messages is None:
            messages = []
        
        # Handle LLMRequestOptions if provided
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
        
        # Extract system prompt and user messages
        system_prompt, user_messages, claude_options = self._extract_system_prompt_and_options(messages, **kwargs)
        
        # Combine user messages into a single query
        # Claude Code SDK expects a single query string
        query = "\n\n".join([msg.get("content", "") for msg in user_messages])
        
        if not query:
            return ChatResult(text='', raw_response=None)
        
        # Execute with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                async with self._create_claude_code_client(
                    system_prompt=system_prompt,
                    max_turns=claude_options.get("max_turns", 1)
                ) as client:
                    text, token_usage = await self._stream_response_to_text(client, query)
                    return ChatResult(
                        text=text,
                        token_usage=token_usage,
                        raw_response={"query": query, "system_prompt": system_prompt}
                    )
                    
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                
                # Check if it's a retriable error
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                
                logger.error(f"Claude Code SDK error: {error_msg}")
                raise
        
        # If all retries exhausted
        if last_exception:
            raise last_exception
        else:
            return ChatResult(text="Failed to get response from Claude Code", raw_response=None)
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error",
            "overloaded"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        if messages is None:
            messages = []
        
        # Extract system prompt and user messages
        system_prompt, user_messages, claude_options = self._extract_system_prompt_and_options(messages, **kwargs)
        
        # Combine user messages into a single query
        query = "\n\n".join([msg.get("content", "") for msg in user_messages])
        
        if not query:
            return
        
        # Stream responses
        try:
            async with self._create_claude_code_client(
                system_prompt=system_prompt,
                max_turns=claude_options.get("max_turns", 1)
            ) as client:
                # Send the query
                await client.query(query)
                
                # Stream responses
                async for message in client.receive_response():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                yield block.text
                                
        except Exception as e:
            logger.error(f"Error streaming Claude Code response: {e}")
            raise
    
    async def get_available_models(self) -> list[str]:
        """Get available Claude Code models."""
        # Claude Code SDK doesn't provide a models API
        # Return default supported models
        return [
            "claude-code",
            "claude-code-sdk",
        ]