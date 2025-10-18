"""Unified Claude Code client with simplified template management."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.base_logger import get_module_logger
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
from dipeo.infrastructure.timing.context import atime_phase, time_phase

from .message_processor import ClaudeCodeMessageProcessor
from .response_parser import ClaudeCodeResponseParser

logger = get_module_logger(__name__)

# Check if fork_session is supported
FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})
FORK_SESSION_ENABLED = (
    FORK_SESSION_SUPPORTED and os.getenv("DIPEO_CLAUDE_FORK_SESSION", "true").lower() == "true"
)


class UnifiedClaudeCodeClient:
    """Unified Claude Code client with fork_session and context manager pattern.

    This client maintains template sessions for each execution phase (for performance)
    and uses context manager pattern for forked sessions (for clean lifecycle management).
    """

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

        # Template sessions for each phase (pre-created for efficiency)
        self._template_sessions: dict[str, ClaudeSDKClient | None] = {
            ExecutionPhase.MEMORY_SELECTION.value: None,
            ExecutionPhase.DIRECT_EXECUTION.value: None,
            "default": None,
        }
        self._template_lock = asyncio.Lock()

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
            from pathlib import Path

            trace_id = kwargs.pop("trace_id", "default")  # Remove trace_id from kwargs
            root = os.getenv("DIPEO_CLAUDE_WORKSPACES", str(BASE_DIR / ".dipeo" / "workspaces"))
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)
        else:
            # Remove trace_id if present since we're not using it
            kwargs.pop("trace_id", None)

    async def _get_or_create_template(
        self, options: ClaudeAgentOptions, execution_phase: str, trace_id: str = ""
    ) -> ClaudeSDKClient:
        """Get or create a template session for the given phase.

        Template sessions are created once and maintained for efficiency.
        They serve as base sessions that can be forked for individual requests.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier
            trace_id: Trace ID for timing metrics

        Returns:
            Template session (not for direct use, should be forked)
        """
        async with self._template_lock:
            # Check if template already exists
            if self._template_sessions.get(execution_phase):
                return self._template_sessions[execution_phase]

            # Enable fork_session for the template if supported
            if FORK_SESSION_ENABLED:
                options.fork_session = True

            # Create and connect template session with timing
            async with atime_phase(
                trace_id,
                "claude_code",
                f"{execution_phase}__template_create",
            ):
                template_session = ClaudeSDKClient(options=options)
                await template_session.connect(None)

            # Store template
            self._template_sessions[execution_phase] = template_session

            return template_session

    async def _get_forked_session_options(
        self, options: ClaudeAgentOptions, execution_phase: str, trace_id: str = ""
    ) -> ClaudeAgentOptions:
        """Get options for a forked session from template.

        Args:
            options: Base Claude Code options
            execution_phase: Execution phase identifier
            trace_id: Trace ID for timing metrics

        Returns:
            ClaudeAgentOptions for forked session, or original if forking not supported
        """
        # Attempt to fork from template if supported
        if FORK_SESSION_ENABLED:
            try:
                # Get or create the template session for this phase
                template = await self._get_or_create_template(options, execution_phase, trace_id)

                # Create fork options with resume from template
                async with atime_phase(trace_id, "claude_code", f"{execution_phase}__fork_prepare"):
                    fork_options = ClaudeAgentOptions(
                        **{
                            **options.__dict__,
                            "resume": template.session_id
                            if hasattr(template, "session_id")
                            else None,
                            "fork_session": True,
                        }
                    )
                return fork_options

            except Exception as e:
                logger.warning(
                    f"[ClaudeCode] Failed to prepare fork from template: {e}, using fresh session"
                )

        # Fallback: Return original options for fresh session
        return options

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
        """Execute async chat completion with simplified template management."""
        # Extract trace_id for timing (removed from kwargs by _setup_workspace)
        trace_id = kwargs.get("trace_id", "")

        # Determine phase key for proper timing attribution
        phase_key = execution_phase.value if execution_phase else "default"

        # Prepare messages for Claude SDK
        async with atime_phase(trace_id, "claude_code", f"{phase_key}__prepare_messages"):
            system_message, formatted_messages = self._processor.prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        async with atime_phase(trace_id, "claude_code", f"{phase_key}__configure_tools"):
            tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase
        async with atime_phase(trace_id, "claude_code", f"{phase_key}__build_system_prompt"):
            system_prompt = self._processor.build_system_prompt(
                system_message,
                execution_phase,
                use_tools,
                **kwargs,
            )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options
        async with atime_phase(trace_id, "claude_code", f"{phase_key}__build_options"):
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
            # Get phase key for this request
            phase_key = execution_phase.value if execution_phase else "default"

            # Get forked session options (with template resume if available)
            forked_options = await self._get_forked_session_options(options, phase_key, trace_id)

            # Create async generator for messages to yield them individually
            async def message_generator():
                for msg in formatted_messages:
                    yield msg

            # Always use async generator for formatted messages
            if formatted_messages:
                query_input = message_generator()
            else:
                # Fallback: create a default message generator
                async def default_generator():
                    yield {
                        "type": "user",
                        "message": json.dumps({"role": "user", "content": "Please respond"}),
                    }

                query_input = default_generator()

            # Execute query with context manager (handles connection/disconnection automatically)
            session_id = f"{phase_key}_{uuid4()}"
            async with (
                atime_phase(trace_id, "claude_code", f"{phase_key}__api_call"),
                ClaudeSDKClient(options=forked_options) as client,
            ):
                # Send query
                async with atime_phase(trace_id, "claude_code", f"{phase_key}__send"):
                    await client.query(query_input)

                # Collect response
                async with atime_phase(trace_id, "claude_code", f"{phase_key}__collect"):
                    result_text, tool_invocation_data = await self._parser.collect_response(
                        client.receive_response()
                    )

                # Parse response
                with time_phase(trace_id, "claude_code", f"{phase_key}__parse"):
                    if tool_invocation_data:
                        parsed = self._parser.parse_response_with_tool_data(
                            tool_invocation_data, execution_phase
                        )
                        parsed.provider = self.provider_type
                        parsed.raw_response = str(tool_invocation_data)
                        return parsed

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
        """Stream chat completion response with simplified template management."""
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

        # Get phase key and forked session options
        phase_key = execution_phase.value if execution_phase else "default"
        trace_id = kwargs.get("trace_id", "")
        forked_options = await self._get_forked_session_options(options, phase_key, trace_id)

        # Create async generator for messages to yield them individually
        async def message_generator():
            for msg in formatted_messages:
                yield msg

        # Always use async generator for formatted messages
        if formatted_messages:
            query_input = message_generator()
        else:
            # Fallback: create a default message generator
            async def default_generator():
                yield {
                    "type": "user",
                    "message": json.dumps({"role": "user", "content": "Please respond"}),
                }

            query_input = default_generator()

        # Execute query with context manager for automatic cleanup
        session_id = f"{phase_key}_{uuid4()}"

        async with ClaudeSDKClient(options=forked_options) as client:
            # Send query
            await client.query(query_input, session_id=session_id)

            # Stream responses
            has_yielded_content = False
            async for message in client.receive_response():
                if hasattr(message, "content") and not hasattr(message, "result"):
                    # Stream content from AssistantMessage (real-time streaming)
                    for block in message.content:
                        # Skip thinking blocks - only stream text content
                        block_type = getattr(block, "type", None)
                        if block_type == "thinking":
                            continue
                        if hasattr(block, "text") and block.text:
                            has_yielded_content = True
                            yield block.text
                elif hasattr(message, "result"):
                    # If we haven't yielded any content yet, yield the result
                    if not has_yielded_content:
                        yield str(message.result)
                    # No need to break - receive_response() auto-terminates after ResultMessage

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

    async def cleanup(self) -> None:
        """Cleanup template sessions on shutdown.

        Note: Forked sessions use context manager pattern and are automatically cleaned up.
        This method only needs to clean up the long-lived template sessions.
        """
        # Clean up template sessions
        async with self._template_lock:
            for phase, template in self._template_sessions.items():
                if template:
                    try:
                        await template.disconnect()
                    except Exception as e:
                        logger.warning(
                            f"[ClaudeCode] Error disconnecting template for phase '{phase}': {e}"
                        )
            self._template_sessions.clear()

        # Give subprocess time to terminate gracefully to avoid EPIPE errors
        await asyncio.sleep(0.5)

        logger.info("[ClaudeCode] Cleanup complete (template sessions)")
