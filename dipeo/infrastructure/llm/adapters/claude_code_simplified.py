"""Simplified Claude Code SDK adapter."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from dipeo.diagram_generated import ChatResult, TokenUsage

from .phase_aware import PhaseAwareAdapter
from .common import ExecutionPhase

logger = logging.getLogger(__name__)


# Phase-specific system prompts
PHASE_PROMPTS = {
    ExecutionPhase.MEMORY_SELECTION: """Return ONLY a JSON array of selected message IDs.
No explanations, no planning, just the array: ["id1", "id2", ...]""",
    
    ExecutionPhase.DIRECT_EXECUTION: """Return ONLY the requested code or execution results.
No explanations, no comments, just the code.""",
    
    ExecutionPhase.DEFAULT: ""
}


class ClaudeCodeAdapter(PhaseAwareAdapter):
    """Simplified adapter for Claude Code SDK."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _initialize_client(self) -> Any:
        # Claude Code SDK doesn't use traditional client initialization
        return None
    
    def supports_tools(self) -> bool:
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
        
        options_dict = {}
        if system_prompt:
            options_dict["system_prompt"] = system_prompt
        if max_turns:
            options_dict["max_turns"] = max_turns
        
        options = ClaudeCodeOptions(**options_dict)
        
        async with ClaudeSDKClient(options=options) as client:
            yield client
    
    def _build_system_prompt(self, user_system: str | None, phase: ExecutionPhase) -> str:
        """Build system prompt based on phase."""
        phase_prompt = PHASE_PROMPTS.get(phase, "")
        
        if phase_prompt and user_system:
            return f"{phase_prompt}\n\n{user_system}"
        elif phase_prompt:
            return phase_prompt
        elif user_system:
            return user_system
        return ""
    
    async def _stream_response(self, client, query: str) -> tuple[str, TokenUsage | None]:
        """Stream response from Claude Code client."""
        full_text = ""
        input_tokens = 0
        output_tokens = 0
        
        try:
            await client.query(query)
            
            async for message in client.receive_messages():
                # Extract text content
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_text += block.text
                
                # Check for end of conversation
                if type(message).__name__ == "ResultMessage":
                    break
                
                # Extract token usage if available
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
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # Use nest_asyncio for nested event loops
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(self.chat_async(messages, **kwargs))
            except RuntimeError:
                # No running loop, use asyncio.run normally
                return asyncio.run(self.chat_async(messages, **kwargs))
        except Exception as e:
            logger.error(f"Error in _make_api_call: {e}")
            raise
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async chat method for Claude Code SDK."""
        if messages is None:
            messages = []
        
        # Process messages with phase awareness
        processed_messages, api_params, execution_phase = self.prepare_request_with_phase(messages, **kwargs)
        
        # Extract system prompt if provided
        user_system_prompt = api_params.pop('_system_prompt', None)
        
        # Build phase-aware system prompt
        system_prompt = self._build_system_prompt(user_system_prompt, execution_phase)
        
        if execution_phase != ExecutionPhase.DEFAULT:
            logger.debug(f"Claude Code using {execution_phase.value} phase")
        
        # Combine messages into query
        query = "\n\n".join([msg.get("content", "") for msg in processed_messages])
        
        if not query:
            return ChatResult(text='', raw_response=None)
        
        # Execute with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                max_turns = api_params.get("max_turns", 1)
                
                async with self._create_claude_code_client(
                    system_prompt=system_prompt,
                    max_turns=max_turns
                ) as client:
                    text, token_usage = await self._stream_response(client, query)
                    
                    return ChatResult(
                        text=text,
                        token_usage=token_usage,
                        raw_response={"phase": execution_phase.value}
                    )
            
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check for rate limit
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                
                # Check for retriable errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                
                logger.error(f"Claude Code SDK error: {error_msg}")
                raise
        
        if last_exception:
            raise last_exception
        
        return ChatResult(text="Failed to get response from Claude Code", raw_response=None)
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        if messages is None:
            messages = []
        
        # Process messages with phase awareness
        processed_messages, api_params, execution_phase = self.prepare_request_with_phase(messages, **kwargs)
        
        # Extract system prompt if provided
        user_system_prompt = api_params.pop('_system_prompt', None)
        
        # Build phase-aware system prompt
        system_prompt = self._build_system_prompt(user_system_prompt, execution_phase)
        
        # Combine messages into query
        query = "\n\n".join([msg.get("content", "") for msg in processed_messages])
        
        if not query:
            return
        
        try:
            max_turns = api_params.get("max_turns", 1)
            
            async with self._create_claude_code_client(
                system_prompt=system_prompt,
                max_turns=max_turns
            ) as client:
                await client.query(query)
                
                async for message in client.receive_messages():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                yield block.text
                    
                    # Check for end
                    if type(message).__name__ == "ResultMessage":
                        break
        
        except Exception as e:
            logger.error(f"Error streaming Claude Code response: {e}")
            raise
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error",
            "overloaded"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    async def get_available_models(self) -> list[str]:
        """Get available Claude Code models."""
        return [
            "claude-code",
            "claude-code-sdk",
        ]