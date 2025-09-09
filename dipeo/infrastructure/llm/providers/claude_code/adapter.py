"""Claude Code adapter implementation using claude-code-sdk."""

import logging
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions

from dipeo.config.llm import CLAUDE_MAX_CONTEXT_LENGTH, CLAUDE_MAX_OUTPUT_TOKENS
from dipeo.config.provider_capabilities import (
    ProviderType as ConfigProviderType,
)
from dipeo.config.provider_capabilities import (
    get_provider_capabilities_object,
)
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.diagram_generated.domain_models import LLMUsage

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
from ...processors import MessageProcessor, ResponseProcessor
from .client import SESSION_POOL_ENABLED, QueryClientWrapper
from .prompts import DIRECT_EXECUTION_PROMPT, LLM_DECISION_PROMPT, MEMORY_SELECTION_PROMPT

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(UnifiedAdapter):
    """Claude Code adapter using claude-code-sdk."""

    def __init__(self, config: AdapterConfig):
        """Initialize Claude Code adapter."""
        # Store config for QueryClientWrapper creation
        self.adapter_config = config

        # Now call parent __init__
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

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Claude Code provider capabilities from centralized config."""
        return get_provider_capabilities_object(
            ConfigProviderType.CLAUDE_CODE,
            max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
            max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
        )

    def _create_sync_client(self):
        """Create synchronous client."""
        # QueryClientWrapper is created per request
        return None

    async def _create_async_client(self):
        """Create asynchronous client."""
        # QueryClientWrapper is created per request
        return None

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

    def _format_messages_as_query(self, messages: list[dict[str, Any]]) -> str:
        """Format messages as JSONL for Claude Code SDK."""
        if not messages:
            return ""

        import json

        # Format each message as JSONL (one JSON object per line)
        jsonl_lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Map role to Claude Code SDK format
            message_type = "assistant" if role == "assistant" else "user"

            # Create the JSON object in Claude Code SDK format
            json_obj = {
                "type": message_type,
                "message": {"role": role, "content": [{"type": "text", "text": content}]},
            }

            # Convert to JSON and add to lines
            jsonl_lines.append(json.dumps(json_obj))

        # Return JSONL format (one JSON object per line)
        return "\n".join(jsonl_lines)

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

        # For Claude Code, we'll pass the execution phase and let the client handle the system prompt
        # This allows proper client reuse with fixed system prompts
        system_prompt = user_system_prompt  # Pass user system prompt directly

        # Phase usage handled silently

        # Add execution phase to kwargs for client
        if execution_phase:
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            kwargs["execution_phase"] = phase_value

        # Note: Synchronous execution not supported with QueryClientWrapper
        # Claude Code SDK's query() is async-only
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we can't use sync
            raise RuntimeError(
                "Synchronous chat not supported in async context. Use async_chat instead."
            )

        # Run the async version synchronously
        return loop.run_until_complete(
            self.async_chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                response_format=response_format,
                execution_phase=execution_phase,
                **kwargs,
            )
        )

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

        # For Claude Code, we'll pass the execution phase and let the client handle the system prompt
        # This allows proper client reuse with fixed system prompts
        system_prompt = user_system_prompt  # Pass user system prompt directly

        # Phase usage handled silently

        # Add execution phase to kwargs for client
        if execution_phase:
            # Handle both string and ExecutionPhase enum
            phase_value = (
                execution_phase.value if hasattr(execution_phase, "value") else execution_phase
            )
            kwargs["execution_phase"] = phase_value

        # Build system prompt based on phase
        final_system_prompt = self._build_system_prompt(system_prompt, execution_phase)

        # Create ClaudeCodeOptions
        options_dict = {}
        if final_system_prompt:
            options_dict["system_prompt"] = final_system_prompt
        options_dict["max_turns"] = kwargs.get("max_turns", 1)
        options_dict["continue_conversation"] = False
        options = ClaudeCodeOptions(**options_dict)

        # Format messages as query
        query = self._format_messages_as_query(prepared_messages)

        # Log if session pooling will be used
        if SESSION_POOL_ENABLED and execution_phase in [
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DIRECT_EXECUTION,
        ]:
            logger.debug(
                f"[ClaudeCodeAdapter] Session pooling eligible for phase {execution_phase}"
            )

        # Execute with QueryClientWrapper
        full_text = ""
        input_tokens = 0
        output_tokens = 0
        metadata = {}

        @self.retry_handler.with_async_retry
        async def _execute():
            nonlocal full_text, input_tokens, output_tokens, metadata
            async with QueryClientWrapper(
                options,
                execution_phase=phase_value if execution_phase else "default",
            ) as wrapper:
                async for message in wrapper.query(query):
                    # Extract content
                    if hasattr(message, "content"):
                        for block in message.content:
                            if hasattr(block, "text"):
                                full_text += block.text

                    # Extract token usage
                    if hasattr(message, "usage"):
                        if hasattr(message.usage, "input_tokens"):
                            input_tokens = message.usage.input_tokens
                        if hasattr(message.usage, "output_tokens"):
                            output_tokens = message.usage.output_tokens

                    # Capture metadata
                    if type(message).__name__ == "ResultMessage":
                        if hasattr(message, "total_cost_usd"):
                            metadata["cost"] = message.total_cost_usd
                        if hasattr(message, "duration_ms"):
                            metadata["duration_ms"] = message.duration_ms

            return full_text

        await _execute()

        # Create token usage
        token_usage = None
        if input_tokens or output_tokens:
            token_usage = LLMUsage(
                input=input_tokens,
                output=output_tokens,
                total=input_tokens + output_tokens,
            )

        # Process response
        response = LLMResponse(
            content=full_text,
            model=self.model,
            provider=ProviderType.ANTHROPIC,
            usage=token_usage,
            raw_response=metadata,
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

        # Process stream chunks from SDK (Message objects) or raw dicts
        async for chunk in stream:
            # SDK Message object
            if (
                hasattr(chunk, "delta")
                and isinstance(chunk.delta, dict)
                and "content" in chunk.delta
            ):
                yield chunk.delta["content"]
            elif hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                yield chunk.content
            # Raw dict fallback
            elif isinstance(chunk, dict):
                delta = chunk.get("delta") or {}
                content = delta.get("content") or chunk.get("content")
                if isinstance(content, str) and content:
                    yield content
