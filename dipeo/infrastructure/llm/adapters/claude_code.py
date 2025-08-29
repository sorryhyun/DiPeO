import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any
from contextlib import asynccontextmanager
from enum import Enum

from dipeo.diagram_generated import (
    ChatResult,
    LLMRequestOptions,
    TokenUsage,
)

from ..drivers.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ExecutionPhase(str, Enum):
    """Execution phases for DiPeO workflows."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


class ClaudeCodeAdapter(BaseLLMAdapter):
    """Adapter for Claude Code SDK with streaming-first architecture."""
    
    # Phase-specific system prompts for DiPeO workflows
    MEMORY_SELECTION_PROMPT = """You are Claude Code integrated into the DiPeO workflow system, specifically optimized for memory selection phases.

When asked to select or analyze memories, data, or context:
1. Provide COMPLETE selections immediately without preliminary planning
2. Return structured, machine-parseable responses
3. Focus solely on the selection criteria and results
4. Exclude meta-commentary about planning or process

Response Format:
- Direct, structured output matching the expected format
- No introductory phrases like "I'll analyze..." or "Let me select..."
- No concluding remarks about next steps
- Pure selection results that can be directly processed
- Start with `[` and close with `]`"""

    DIRECT_EXECUTION_PROMPT = """You are Claude Code integrated into the DiPeO workflow system, specifically optimized for direct code execution and generation.

When asked to generate code or execute tasks:
1. Return ONLY the requested code or execution results
2. Provide COMPLETE, WORKING implementations
3. Skip ALL planning, introduction, or explanation phases
4. Deliver production-ready code immediately

Code Generation Rules:
- NO placeholders, TODOs, or "implementation here" comments
- COMPLETE all functions, methods, and logic
- Include ALL necessary imports and dependencies
- Implement ACTUAL functionality, not stubs
- Handle errors and edge cases properly

Response Format:
- Raw code files in the exact format requested
- No conversational text before or after code
- No self-descriptions like 'Looking at the code, I need to..."
- No explanations unless explicitly requested"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0
        self._active_clients = {}  # Track active client contexts
        self._client_lock = asyncio.Lock()
        
        # Create logs directory if it doesn't exist
        self.logs_dir = Path(".logs")
        self.logs_dir.mkdir(exist_ok=True)
    
    def _build_system_prompt(
        self, 
        user_system_prompt: str | None = None,
        execution_phase: str | ExecutionPhase | None = None
    ) -> str:
        """Build the complete system prompt based on execution phase and user input.
        
        Args:
            user_system_prompt: Optional user-provided system prompt to append
            execution_phase: The execution phase (memory_selection, direct_execution, or default)
            
        Returns:
            Complete system prompt combining phase-specific defaults and user prompts
        """
        # Convert string to enum if needed
        if isinstance(execution_phase, str):
            try:
                execution_phase = ExecutionPhase(execution_phase)
            except ValueError:
                execution_phase = ExecutionPhase.DEFAULT
        
        # Select base prompt based on phase
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            base_prompt = self.MEMORY_SELECTION_PROMPT
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            base_prompt = self.DIRECT_EXECUTION_PROMPT
        else:
            # Default or None - no base prompt
            base_prompt = ""
        
        # Combine base and user prompts
        if base_prompt and user_system_prompt:
            return f"{base_prompt}\n\n{user_system_prompt}"
        elif base_prompt:
            return base_prompt
        elif user_system_prompt:
            return user_system_prompt
        else:
            return ""
    
        
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
        """Extract system prompt and options from messages and kwargs.
        
        Args:
            messages: Input messages
            **kwargs: Additional parameters including optional execution_phase
            
        Returns:
            Tuple of (complete_system_prompt, user_messages, claude_options)
        """
        user_system_prompt = ""
        user_messages = []
        
        # Extract user system prompt from messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                user_system_prompt = content
            elif role == "user":
                user_messages.append(msg)
            # Note: Claude Code SDK handles conversation context internally
        
        # Get explicitly provided execution phase (default to DEFAULT if not provided)
        execution_phase = kwargs.get('execution_phase', ExecutionPhase.DEFAULT)
        
        # Build complete system prompt using consolidated logic
        system_prompt = self._build_system_prompt(
            user_system_prompt=user_system_prompt,
            execution_phase=execution_phase
        )
        
        # Log phase usage for debugging
        if execution_phase != ExecutionPhase.DEFAULT:
            phase_str = execution_phase.value if hasattr(execution_phase, 'value') else str(execution_phase)
            logger.debug(f"Claude Code adapter using {phase_str} phase")
            
        # Extract Claude Code specific options
        claude_code_options = {
            "max_turns": kwargs.get("max_turns", 1),
        }
        
        return system_prompt, user_messages, claude_code_options
    
    async def _stream_response_to_text(self, client, query: str) -> tuple[str, TokenUsage | None, dict | None]:
        """Stream response from Claude Code client and collect text with metadata.
        
        Returns:
            Tuple of (full_text, token_usage, metadata_dict)
        """
        full_text = ""
        input_tokens = 0
        output_tokens = 0
        metadata = {}
        
        try:
            # Send the query
            await client.query(query)
            
            # Stream and collect responses
            async for message in client.receive_messages():
                # Extract content if available
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_text += block.text
                
                # Capture ResultMessage metadata (simplified)
                if type(message).__name__ == "ResultMessage":
                    # Only capture simple, serializable metadata
                    if hasattr(message, 'total_cost_usd'):
                        metadata["cost"] = message.total_cost_usd
                    if hasattr(message, 'duration_ms'):
                        metadata["duration_ms"] = message.duration_ms
                    if hasattr(message, 'num_turns'):
                        metadata["num_turns"] = message.num_turns
                    if hasattr(message, 'session_id'):
                        metadata["session_id"] = str(message.session_id) if message.session_id else None
                    
                    # ResultMessage indicates the end of the conversation
                    break
                
                # Try to extract token usage
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
        
        # Keep metadata simple and serializable
        metadata["response_length"] = len(full_text)
        
        return full_text, token_usage, metadata
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Synchronous wrapper for async Claude Code API calls."""
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use nest_asyncio to allow nested event loops
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(self.chat_async(messages, **kwargs))
            except RuntimeError:
                # No running loop, we can use asyncio.run normally
                return asyncio.run(self.chat_async(messages, **kwargs))
        except Exception as e:
            logger.error(f"Error in _make_api_call: {e}")
            raise
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async chat method for Claude Code SDK."""
        if messages is None:
            messages = []
        
        # Extract execution_phase before it gets validated
        # This parameter is used internally but not passed to the SDK
        execution_phase = kwargs.pop('execution_phase', None)
        if execution_phase:
            # Re-add it for internal use by _extract_system_prompt_and_options
            kwargs['execution_phase'] = execution_phase
        
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
                    text, token_usage, metadata = await self._stream_response_to_text(client, query)
                    
                    # Prepare simplified log data
                    log_data = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": self.model_name,
                        "query_length": len(query),
                        "response_length": len(text),
                        "token_usage": {
                            "input": token_usage.input if token_usage else None,
                            "output": token_usage.output if token_usage else None,
                            "total": token_usage.total if token_usage else None
                        } if token_usage else None,
                        "metadata": metadata,  # Already simplified in _stream_response_to_text
                        "execution_phase": kwargs.get('execution_phase', 'default')
                    }
                    
                    # Save to JSON log (non-blocking)
                    self._save_json_log(log_data, "chat")
                    
                    return ChatResult(
                        text=text,
                        token_usage=token_usage,
                        raw_response=metadata  # Simplified metadata
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
    
    def _save_json_log(self, data: dict, log_type: str = "chat") -> None:
        """Save interaction data as JSON log.
        
        Args:
            data: Dictionary containing the interaction data
            log_type: Type of log (chat, stream, etc.)
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            filename = self.logs_dir / f"claude_code_{log_type}_{timestamp}.json"
            
            # Ensure data is JSON serializable with safer approach
            def make_serializable(obj):
                try:
                    # Try direct JSON serialization first
                    json.dumps(obj)
                    return obj
                except:
                    # For datetime objects
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    # For objects with __dict__
                    elif hasattr(obj, '__dict__'):
                        # Only include simple types from __dict__
                        return {k: v for k, v in obj.__dict__.items() 
                                if isinstance(v, (str, int, float, bool, type(None)))}
                    # Fallback to string representation
                    else:
                        return str(obj)
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=make_serializable)
                
            logger.debug(f"Saved Claude Code interaction log to {filename}")
            
        except Exception as e:
            # Don't let logging errors break the main flow
            logger.debug(f"Skipped saving JSON log due to: {e}")
    
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
                
                # Simplified streaming data for logging
                full_response = ""
                stream_metadata = {}
                
                # Stream responses
                async for message in client.receive_messages():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                full_response += block.text
                                yield block.text
                    
                    # Capture simple metadata from ResultMessage
                    if type(message).__name__ == "ResultMessage":
                        if hasattr(message, 'total_cost_usd'):
                            stream_metadata["cost"] = message.total_cost_usd
                        if hasattr(message, 'duration_ms'):
                            stream_metadata["duration_ms"] = message.duration_ms
                        if hasattr(message, 'num_turns'):
                            stream_metadata["num_turns"] = message.num_turns
                        
                        # ResultMessage indicates the end of the conversation
                        break
                
                # Save simplified stream log after completion
                stream_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": self.model_name,
                    "query_length": len(query),
                    "response_length": len(full_response),
                    "metadata": stream_metadata,
                    "execution_phase": kwargs.get('execution_phase', 'default')
                }
                self._save_json_log(stream_data, "stream")
                                
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