"""Unified Claude Code client that merges adapter and wrapper layers."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    CLAUDE_MAX_CONTEXT_LENGTH,
    CLAUDE_MAX_OUTPUT_TOKENS,
)
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
            root = os.getenv(
                "DIPEO_CLAUDE_WORKSPACES", os.path.join(os.getcwd(), ".dipeo", "workspaces")
            )
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)
        else:
            # Remove trace_id if present since we're not using it
            kwargs.pop("trace_id", None)

    def _build_claude_options(
        self,
        system_prompt: str | None,
        tool_options: dict,
        hooks_config: dict | None,
        stream: bool = False,
        **kwargs,
    ) -> ClaudeCodeOptions:
        """Build Claude Code options dictionary."""
        options_dict = {
            "system_prompt": system_prompt,
        }

        # Add streaming flag if specified
        if stream:
            options_dict["stream"] = True

        # Add MCP server and allowed tools if configured
        if "mcp_server" in tool_options:
            options_dict["mcp_servers"] = {"dipeo_structured_output": tool_options["mcp_server"]}
            options_dict["allowed_tools"] = tool_options.get("allowed_tools", [])

        # Add hook configuration if provided
        if hooks_config:
            hooks_dict = self._processor.format_hooks_config(hooks_config)
            options_dict.update(hooks_dict)

        # Add other kwargs (but remove text_format and person_name if present)
        kwargs.pop("text_format", None)  # Remove text_format as we don't use it
        kwargs.pop("person_name", None)  # Remove person_name as it's already used in system prompt
        options_dict.update(kwargs)

        # Create options
        return ClaudeCodeOptions(**options_dict)

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
        system_message, serialized_messages = self._processor.prepare_message(messages)

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
        options = self._build_claude_options(
            system_prompt, tool_options, hooks_config, stream=False, **kwargs
        )

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
                execution_phase=str(execution_phase) if execution_phase else "default",
            ) as wrapper:
                # Collect messages and detect tool invocations
                # When MCP tools are used, we need to capture the tool input data
                # which contains our structured output, not the final text response
                result_text = ""
                tool_invocation_data = None

                async for message in wrapper.query(serialized_messages):
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
        system_message, serialized_messages = self._processor.prepare_message(messages)

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
        options = self._build_claude_options(
            system_prompt, tool_options, hooks_config, stream=True, **kwargs
        )

        # Use QueryClientWrapper with context manager
        async with SessionQueryWrapper(
            options=options, execution_phase=str(execution_phase) if execution_phase else "default"
        ) as wrapper:
            # Stream messages from Claude Code SDK
            # For streaming, we need to handle both AssistantMessage (for real-time streaming)
            # and ResultMessage (for final result)
            has_yielded_content = False
            async for message in wrapper.query(serialized_messages):
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
