"""Unified Claude Code client that merges adapter and wrapper layers."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeAgentOptions
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    CLAUDE_MAX_CONTEXT_LENGTH,
    CLAUDE_MAX_OUTPUT_TOKENS,
)
from dipeo.config.paths import BASE_DIR
from dipeo.config.provider_capabilities import get_provider_capabilities_object
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)

from .message_processor import ClaudeCodeMessageProcessor
from .response_parser import ClaudeCodeResponseParser
from .transport.session_wrapper import SessionQueryWrapper

logger = logging.getLogger(__name__)

# Session pooling configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"


class UnifiedClaudeCodeClient:
    """Unified Claude Code client that combines adapter and wrapper functionality."""

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config

        # Import the config ProviderType
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        self.provider_type = ConfigProviderType.CLAUDE_CODE

        # Set capabilities
        self.capabilities = self._get_capabilities()

        # Initialize retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        # Initialize helper classes
        self._parser = ClaudeCodeResponseParser()
        self._processor = ClaudeCodeMessageProcessor()

        logger.info(f"[ClaudeCode] Initialized with SESSION_POOL_ENABLED={SESSION_POOL_ENABLED}")

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Claude Code provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.CLAUDE_CODE,
            max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
            max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
        )

    def _setup_workspace(self, kwargs: dict) -> None:
        """Set up workspace directory for claude-code if not already configured.

        Modifies kwargs in-place to add 'cwd' if not present.
        """
        if "cwd" not in kwargs:
            import os
            from pathlib import Path

            trace_id = kwargs.pop("trace_id", "default")  # Remove trace_id from kwargs
            root = os.getenv("DIPEO_CLAUDE_WORKSPACES", str(BASE_DIR / ".dipeo" / "workspaces"))
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)
        else:
            # Remove trace_id if present since we're not using it
            kwargs.pop("trace_id", None)

    async def async_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        hooks_config: dict[str, list[dict]] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute async chat completion with retry logic."""
        # Prepare messages for Claude SDK
        logger.debug(
            "[ClaudeCode] Preparing %d messages for phase %s",
            len(messages),
            execution_phase,
        )
        system_message, formatted_messages = self._processor.prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase
        system_prompt = self._processor.build_system_prompt(
            system_message,
            execution_phase,
            use_tools,
            **kwargs,
        )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options
        options_dict = self._processor.build_claude_options(
            system_prompt, tool_options, hooks_config, stream=False, **kwargs
        )
        options = ClaudeAgentOptions(**options_dict)

        # Set up retry logic
        retry = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.retry_delay,
                min=self.retry_delay,
                max=self.retry_delay * (self.retry_backoff**self.max_retries),
            ),
            retry=retry_if_exception_type(Exception),
        )

        async def _make_request():
            # Use QueryClientWrapper with context manager
            async with SessionQueryWrapper(
                options=options,
                execution_phase=execution_phase.value if execution_phase else "default",
            ) as wrapper:
                # Collect messages and detect tool invocations
                # When MCP tools are used, we need to capture the tool input data
                # which contains our structured output, not the final text response
                result_text = ""
                tool_invocation_data = None

                # Combine all messages into a single user prompt string
                # This avoids issues with assistant messages and AsyncIterable mode
                combined_content = []

                for msg in formatted_messages:
                    message_data = json.loads(msg["message"])
                    role = message_data.get("role", msg["type"])

                    # Extract content text
                    content_text = ""
                    if isinstance(message_data.get("content"), str):
                        content_text = message_data["content"]
                    elif isinstance(message_data.get("content"), list):
                        # Extract text from content blocks
                        text_parts = []
                        for block in message_data["content"]:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        content_text = " ".join(text_parts)

                    # Format the message with role prefix for multi-message conversations
                    if len(formatted_messages) > 1:
                        # Include role prefix for context
                        if role == "assistant":
                            combined_content.append(f"Assistant: {content_text}")
                        elif role == "user":
                            combined_content.append(f"User: {content_text}")
                        else:
                            combined_content.append(content_text)
                    else:
                        # Single message - just use the content directly
                        combined_content.append(content_text)

                # Join all messages into a single prompt string
                query_input = (
                    "\n\n".join(combined_content) if combined_content else "Please respond"
                )

                async for message in wrapper.query(query_input):
                    # Check for tool invocations in assistant messages
                    if hasattr(message, "content") and not hasattr(message, "result"):
                        # Check if this message contains tool invocations
                        for block in message.content:
                            if hasattr(block, "name") and hasattr(block, "input"):
                                # This is a tool invocation - extract the input data
                                if block.name.startswith("mcp__dipeo_structured_output__"):
                                    logger.debug(
                                        f"[ClaudeCode] Found MCP tool invocation: {block.name} "
                                        f"with input: {block.input}"
                                    )
                                    # Store the tool input data which contains our structured output
                                    tool_invocation_data = block.input
                                    # For MCP tools, the input IS the output we want
                                    break

                    # Process ResultMessage as final fallback
                    if hasattr(message, "result"):
                        result_text = str(message.result)
                        break  # We have the result

                # If we found tool invocation data, use it directly
                if tool_invocation_data:
                    logger.debug(
                        f"[ClaudeCode] Using tool invocation data as response for {execution_phase}: "
                        f"{tool_invocation_data}"
                    )
                    parsed = self._parser.parse_response_with_tool_data(
                        tool_invocation_data, execution_phase
                    )
                    parsed.provider = self.provider_type
                    parsed.raw_response = str(tool_invocation_data)
                    return parsed

                # Otherwise, parse the text response as before
                parsed = self._parser.parse_response(result_text, execution_phase)
                parsed.provider = self.provider_type
                parsed.raw_response = result_text
                return parsed

        async for attempt in retry:
            with attempt:
                return await _make_request()

        # Should never reach here due to retry logic
        raise RuntimeError("Failed to get response after retries")

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        hooks_config: dict[str, list[dict]] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        # Prepare messages for Claude SDK
        system_message, formatted_messages = self._processor.prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase
        system_prompt = self._processor.build_system_prompt(
            system_message,
            execution_phase,
            use_tools,
            **kwargs,
        )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options with streaming
        options_dict = self._processor.build_claude_options(
            system_prompt, tool_options, hooks_config, stream=True, **kwargs
        )
        options = ClaudeAgentOptions(**options_dict)

        # Use QueryClientWrapper with context manager
        async with SessionQueryWrapper(
            options=options, execution_phase=execution_phase.value if execution_phase else "default"
        ) as wrapper:
            # Stream messages from Claude Code SDK
            # For streaming, we need to handle both AssistantMessage (for real-time streaming)
            # and ResultMessage (for final result)
            has_yielded_content = False

            # Create async generator for messages if multiple messages exist
            async def message_generator():
                for msg in formatted_messages:
                    yield json.dumps(msg, ensure_ascii=False)

            # Use async iterable if we have multiple messages, otherwise use JSON string
            if len(formatted_messages) > 1:
                query_input = message_generator()
            else:
                query_input = json.dumps(formatted_messages, ensure_ascii=False)

            async for message in wrapper.query(query_input):
                if hasattr(message, "content") and not hasattr(message, "result"):
                    # Stream content from AssistantMessage (real-time streaming)
                    for block in message.content:
                        if hasattr(block, "text") and block.text:
                            has_yielded_content = True
                            yield block.text
                elif hasattr(message, "result"):
                    # If we haven't yielded any content yet, yield the result
                    # This handles non-streaming responses
                    if not has_yielded_content:
                        yield str(message.result)
                    break  # ResultMessage is the final message

    async def batch_chat(
        self,
        messages_list: list[list[Message]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> list[LLMResponse]:
        """Execute batch chat completion requests."""
        # Claude Code doesn't have native batch API, so we process with asyncio.gather
        tasks = [
            self.async_chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                response_format=response_format,
                execution_phase=execution_phase,
                **kwargs,
            )
            for messages in messages_list
        ]

        return await asyncio.gather(*tasks)
