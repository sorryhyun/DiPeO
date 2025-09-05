"""Claude Code adapter implementation using claude-code-sdk."""

import logging
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any

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
    TokenUsage,
)
from ...processors import MessageProcessor, ResponseProcessor, TokenCounter
from .client import AsyncClaudeCodeClientWrapper, ClaudeCodeClientWrapper
from .prompts import DIRECT_EXECUTION_PROMPT, LLM_DECISION_PROMPT, MEMORY_SELECTION_PROMPT

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(UnifiedAdapter):
    """Claude Code adapter using claude-code-sdk."""

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
                backoff_factor=config.retry_backoff or 2.0,
            ),
        )
        self.streaming_handler = StreamingHandler(
            ProviderType.ANTHROPIC, StreamConfig(mode=config.streaming_mode or StreamingMode.SSE)
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
            streaming_modes={StreamingMode.SSE},
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
        self, user_system_prompt: str | None = None, execution_phase: ExecutionPhase | None = None
    ) -> str:
        """Build complete system prompt based on execution phase."""
        # Convert string to ExecutionPhase enum if needed
        if execution_phase and isinstance(execution_phase, str):
            try:
                execution_phase = ExecutionPhase(execution_phase)
            except ValueError:
                # If invalid phase, default to DEFAULT
                execution_phase = ExecutionPhase.DEFAULT

        # Map ExecutionPhase to ClaudeCodeExecutionPhase
        phase_prompt = ""

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            # Extract assistant name from user_system_prompt if available
            assistant_name = "Claude"  # Default name
            if user_system_prompt and "YOUR NAME:" in user_system_prompt:
                match = re.match(r"YOUR NAME:\s*([^\n]+)", user_system_prompt)
                if match:
                    assistant_name = match.group(1).strip()
                    # Remove the YOUR NAME line from user_system_prompt to avoid duplication
                    user_system_prompt = re.sub(
                        r"YOUR NAME:\s*[^\n]+\n*", "", user_system_prompt
                    ).strip()
            # Format the prompt with the assistant name
            phase_prompt = MEMORY_SELECTION_PROMPT.format(assistant_name=assistant_name)
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            phase_prompt = DIRECT_EXECUTION_PROMPT
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            phase_prompt = LLM_DECISION_PROMPT

        # Combine prompts
        if phase_prompt and user_system_prompt:
            return f"{phase_prompt}\n\n{user_system_prompt}"
        elif phase_prompt:
            return phase_prompt
        elif user_system_prompt:
            return user_system_prompt
        else:
            return ""

    def prepare_messages(self, messages: list[Message]) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare messages for Claude Code SDK, extracting system prompt."""
        # Extract system prompt
        system_prompt = self.message_processor.extract_system_prompt(messages)

        # Filter out system messages and process the rest
        non_system_messages = []
        for msg in messages:
            # Handle both Message objects and dictionaries
            if isinstance(msg, dict):
                if msg.get("role") != "system":
                    non_system_messages.append(msg)
            elif hasattr(msg, "role") and msg.role != "system":
                non_system_messages.append(msg)

        prepared_messages = self.message_processor.prepare_messages(non_system_messages)

        return prepared_messages, system_prompt

    def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
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
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            logger.debug(f"Claude Code adapter using {phase_value} phase")

        # Add execution phase to kwargs for client
        if execution_phase:
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            kwargs["execution_phase"] = phase_value

        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs,
            )

        raw_response = _execute()

        # Extract token usage from response
        token_usage = None
        if "usage" in raw_response:
            usage_data = raw_response["usage"]
            token_usage = TokenUsage(
                input_tokens=usage_data.get("prompt_tokens", 0),
                output_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        # Process response
        response = LLMResponse(
            content=raw_response.get("content", ""),
            model=self.model,
            provider=ProviderType.ANTHROPIC,
            usage=token_usage,
            raw_response=raw_response.get("metadata"),
        )

        return response

    async def async_chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
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
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            logger.debug(f"Claude Code adapter using {phase_value} phase")

        # Add execution phase to kwargs for client
        if execution_phase:
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            kwargs["execution_phase"] = phase_value

        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs,
            )

        raw_response = await _execute()

        # Extract token usage from response
        token_usage = None
        if "usage" in raw_response:
            usage_data = raw_response["usage"]
            token_usage = TokenUsage(
                input_tokens=usage_data.get("prompt_tokens", 0),
                output_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        # Process response
        response = LLMResponse(
            content=raw_response.get("content", ""),
            model=self.model,
            provider=ProviderType.ANTHROPIC,
            usage=token_usage,
            raw_response=raw_response.get("metadata"),
        )

        return response

    def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        raise NotImplementedError("Synchronous streaming not supported for Claude Code SDK")

    async def async_stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
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
                **kwargs,
            )

        stream = await _execute()

        # Process stream chunks
        async for chunk in stream:
            if isinstance(chunk, dict) and "delta" in chunk and "content" in chunk["delta"]:
                yield chunk["delta"]["content"]
