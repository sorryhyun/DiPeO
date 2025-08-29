"""Claude Code adapter implementation using claude-code-sdk."""

import logging
from enum import Enum
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from dipeo.diagram_generated import Message, ToolConfig

from ...capabilities import (
    RetryHandler,
    StreamingHandler,
)
from ...core.adapter import UnifiedAdapter
from ...core.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
    ProviderType,
    RetryConfig,
    StreamConfig,
    StreamingMode,
)
from ...processors import MessageProcessor, ResponseProcessor, TokenCounter
from .client import AsyncClaudeCodeClientWrapper, ClaudeCodeClientWrapper

logger = logging.getLogger(__name__)


class ClaudeCodeExecutionPhase(str, Enum):
    """Claude Code specific execution phases."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


class ClaudeCodeAdapter(UnifiedAdapter):
    """Claude Code adapter using claude-code-sdk."""
    
    # Phase-specific system prompts
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
- No explanations unless explicitly requested
- No "Here's the implementation..." introductions
- No "This code does..." summaries"""
    
    def __init__(self, config: AdapterConfig):
        """Initialize Claude Code adapter."""
        # Initialize clients first (needed by parent __init__)
        self.sync_client_wrapper = ClaudeCodeClientWrapper(config)
        self.async_client_wrapper = AsyncClaudeCodeClientWrapper(config)
        
        # Now call parent __init__ which will use _create_sync_client and _create_async_client
        super().__init__(config)
        
        # Initialize capabilities (limited compared to standard Anthropic)
        self.retry_handler = RetryHandler(
            ProviderType.ANTHROPIC,  # Reuse Anthropic provider type for now
            RetryConfig(
                max_attempts=config.max_retries or 3,
                initial_delay=config.retry_delay or 1.0,
                backoff_factor=config.retry_backoff or 2.0
            )
        )
        self.streaming_handler = StreamingHandler(
            ProviderType.ANTHROPIC,
            StreamConfig(mode=config.streaming_mode or StreamingMode.SSE)
        )
        
        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.ANTHROPIC)
        self.response_processor = ResponseProcessor(ProviderType.ANTHROPIC)
        self.token_counter = TokenCounter(ProviderType.ANTHROPIC)
    
    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Claude Code provider capabilities."""
        return ProviderCapabilities(
            supports_async=True,
            supports_streaming=True,
            supports_tools=False,  # Claude Code SDK doesn't support tools in the same way
            supports_structured_output=False,  # Limited structured output support
            supports_vision=False,
            supports_web_search=False,
            supports_image_generation=False,
            supports_computer_use=True,  # Claude Code specific capability
            max_context_length=200000,
            max_output_tokens=8192,
            supported_models={
                "claude-code",
                "claude-code-sdk",
            },
            streaming_modes={StreamingMode.SSE}
        )
    
    def _create_sync_client(self):
        """Create synchronous client."""
        return self.sync_client_wrapper
    
    async def _create_async_client(self):
        """Create asynchronous client."""
        return self.async_client_wrapper
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        return model in self.capabilities.supported_models or model.startswith("claude-code")
    
    def _build_system_prompt(
        self,
        user_system_prompt: Optional[str] = None,
        execution_phase: Optional[ExecutionPhase] = None
    ) -> str:
        """Build complete system prompt based on execution phase."""
        # Map ExecutionPhase to ClaudeCodeExecutionPhase
        phase_prompt = ""
        
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            phase_prompt = self.MEMORY_SELECTION_PROMPT
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            phase_prompt = self.DIRECT_EXECUTION_PROMPT
        
        # Combine prompts
        if phase_prompt and user_system_prompt:
            return f"{phase_prompt}\n\n{user_system_prompt}"
        elif phase_prompt:
            return phase_prompt
        elif user_system_prompt:
            return user_system_prompt
        else:
            return ""
    
    def prepare_messages(self, messages: List[Message]) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Prepare messages for Claude Code SDK, extracting system prompt."""
        # Extract system prompt
        system_prompt = self.message_processor.extract_system_prompt(messages)
        
        # Filter out system messages and process the rest
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        prepared_messages = self.message_processor.prepare_messages(non_system_messages)
        
        return prepared_messages, system_prompt
    
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        response_format: Optional[Any] = None,
        execution_phase: Optional[ExecutionPhase] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute synchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages and extract system prompt
        prepared_messages, user_system_prompt = self.prepare_messages(messages)
        
        # Build complete system prompt with phase
        system_prompt = self._build_system_prompt(user_system_prompt, execution_phase)
        
        # Log phase usage
        if execution_phase and execution_phase != ExecutionPhase.DEFAULT:
            logger.debug(f"Claude Code adapter using {execution_phase.value} phase")
        
        # Add execution phase to kwargs for client
        if execution_phase:
            kwargs['execution_phase'] = execution_phase.value
        
        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        raw_response = _execute()
        
        # Process response
        response = LLMResponse(
            text=raw_response.get("content", ""),
            raw_response=raw_response.get("metadata"),
            token_usage=self.token_counter.extract_token_usage(raw_response, self.model)
        )
        
        return response
    
    async def async_chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        response_format: Optional[Any] = None,
        execution_phase: Optional[ExecutionPhase] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute asynchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages and extract system prompt
        prepared_messages, user_system_prompt = self.prepare_messages(messages)
        
        # Build complete system prompt with phase
        system_prompt = self._build_system_prompt(user_system_prompt, execution_phase)
        
        # Log phase usage
        if execution_phase and execution_phase != ExecutionPhase.DEFAULT:
            logger.debug(f"Claude Code adapter using {execution_phase.value} phase")
        
        # Add execution phase to kwargs for client
        if execution_phase:
            kwargs['execution_phase'] = execution_phase.value
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        raw_response = await _execute()
        
        # Process response
        response = LLMResponse(
            text=raw_response.get("content", ""),
            raw_response=raw_response.get("metadata"),
            token_usage=self.token_counter.extract_token_usage(raw_response, self.model)
        )
        
        return response
    
    def stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        **kwargs
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        raise NotImplementedError("Synchronous streaming not supported for Claude Code SDK")
    
    async def async_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream asynchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages and extract system prompt
        prepared_messages, user_system_prompt = self.prepare_messages(messages)
        
        # Build system prompt (no execution phase for streaming)
        system_prompt = self._build_system_prompt(user_system_prompt, None)
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        stream = await _execute()
        
        # Process stream chunks
        async for chunk in stream:
            if isinstance(chunk, dict) and "delta" in chunk:
                if "content" in chunk["delta"]:
                    yield chunk["delta"]["content"]