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
    """Unified Claude Code client with efficient template-based session management.

    This client maintains pre-created template sessions for each execution phase
    and forks them for individual requests. This provides both efficiency (no cold start)
    and isolation (each request gets its own forked session).
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

        # Track active forked sessions for cleanup
        self._active_sessions: list[ClaudeSDKClient] = []
        self._session_lock = asyncio.Lock()

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

    async def _create_forked_session(
        self, options: ClaudeAgentOptions, execution_phase: str, trace_id: str = ""
    ) -> ClaudeSDKClient:
        """Create a session by forking from template or creating fresh.

        This method attempts to fork from an existing template session for efficiency.
        If forking is not supported or fails, it falls back to creating a fresh session.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier
            trace_id: Trace ID for timing metrics

        Returns:
            New or forked ClaudeSDKClient session for this request
        """
        # Attempt to get/create template and fork from it if supported
        if FORK_SESSION_ENABLED:
            try:
                # Get or create the template session for this phase
                template = await self._get_or_create_template(options, execution_phase, trace_id)

                # Create a forked session from the template
                # The fork will inherit the template's configuration but have its own state
                # Create new session with resume from template (this creates a fork)
                async with atime_phase(
                    trace_id,
                    "claude_code",
                    f"{execution_phase}__fork",
                ):
                    fork_options = ClaudeAgentOptions(
                        **{
                            **options.__dict__,
                            "resume": template.session_id
                            if hasattr(template, "session_id")
                            else None,
                            "fork_session": True,
                        }
                    )

                    forked_session = ClaudeSDKClient(options=fork_options)
                    await forked_session.connect(None)

                # Track the forked session for cleanup
                async with self._session_lock:
                    self._active_sessions.append(forked_session)

                return forked_session

            except Exception as e:
                logger.warning(
                    f"[ClaudeCode] Failed to fork from template: {e}, creating fresh session"
                )

        # Fallback: Create a fresh session if forking is not available or failed
        logger.debug(f"[ClaudeCode] Creating fresh session for phase '{execution_phase}'")

        async with atime_phase(
            trace_id,
            "claude_code",
            f"{execution_phase}__fresh_create",
        ):
            session = ClaudeSDKClient(options=options)
            await session.connect(None)

        # Track session for cleanup
        async with self._session_lock:
            self._active_sessions.append(session)

        return session

    async def _execute_query(
        self,
        session: ClaudeSDKClient,
        query_input: str | AsyncIterator[dict[str, Any]],
        execution_phase: ExecutionPhase | None,
        session_id: str,
        trace_id: str = "",
    ) -> LLMResponse:
        """Execute a query on a session.

        Args:
            session: ClaudeSDKClient session to query
            query_input: Message dict or async iterable of message dicts to send
            execution_phase: Execution phase for response parsing
            session_id: Unique session ID for this query
            trace_id: Trace ID for timing metrics

        Returns:
            Parsed LLM response
        """
        phase_key = execution_phase.value if execution_phase else "default"

        try:
            # Send query with unique session ID
            async with atime_phase(trace_id, "claude_code", "llm_response__send"):
                await session.query(query_input, session_id=session_id)

            # Collect response
            result_text = ""
            tool_invocation_data = None

            async with atime_phase(trace_id, "claude_code", "llm_response__collect"):
                async for message in session.receive_response():
                    # Check for tool invocations
                    if hasattr(message, "content") and not hasattr(message, "result"):
                        for block in message.content:
                            if hasattr(block, "name") and hasattr(block, "input"):
                                if block.name.startswith("mcp__dipeo_structured_output__"):
                                    tool_invocation_data = block.input
                                    break

                    # Process ResultMessage (final message, iterator auto-terminates after this)
                    if hasattr(message, "result"):
                        result_text = str(message.result)
                        # No need to break - receive_response() auto-terminates

            # Parse response
            with time_phase(trace_id, "claude_code", "llm_response__parse"):
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
        finally:
            # Clean up session after use
            with time_phase(trace_id, "claude_code", "llm_response__cleanup"):
                await self._cleanup_session(session)

    async def _cleanup_session(self, session: ClaudeSDKClient) -> None:
        """Clean up a session after use."""
        try:
            await session.disconnect()
            async with self._session_lock:
                if session in self._active_sessions:
                    self._active_sessions.remove(session)
        except Exception as e:
            logger.warning(f"[ClaudeCode] Error disconnecting session: {e}")

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

        # Prepare messages for Claude SDK
        async with atime_phase(trace_id, "claude_code", "request__prepare_messages"):
            system_message, formatted_messages = self._processor.prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        async with atime_phase(trace_id, "claude_code", "request__configure_tools"):
            tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase
        async with atime_phase(trace_id, "claude_code", "request__build_system_prompt"):
            system_prompt = self._processor.build_system_prompt(
                system_message,
                execution_phase,
                use_tools,
                **kwargs,
            )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options
        async with atime_phase(trace_id, "claude_code", "request__build_options"):
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
            # Fork from template or create fresh session for this request
            phase_key = execution_phase.value if execution_phase else "default"
            session = await self._create_forked_session(options, phase_key, trace_id)

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

            # Execute query with unique session ID
            session_id = f"{phase_key}_{uuid4()}"
            async with atime_phase(
                trace_id,
                "claude_code",
                f"{phase_key}__api_call",
            ):
                return await self._execute_query(
                    session, query_input, execution_phase, session_id, trace_id
                )

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

        # Fork from template or create fresh session for this request
        phase_key = execution_phase.value if execution_phase else "default"
        session = await self._create_forked_session(options, phase_key)

        try:
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

            # Execute query with unique session ID
            session_id = f"{phase_key}_{uuid4()}"
            await session.query(query_input, session_id=session_id)

            # Stream responses
            has_yielded_content = False
            async for message in session.receive_response():
                if hasattr(message, "content") and not hasattr(message, "result"):
                    # Stream content from AssistantMessage (real-time streaming)
                    for block in message.content:
                        if hasattr(block, "text") and block.text:
                            has_yielded_content = True
                            yield block.text
                elif hasattr(message, "result"):
                    # If we haven't yielded any content yet, yield the result
                    if not has_yielded_content:
                        yield str(message.result)
                    # No need to break - receive_response() auto-terminates after ResultMessage
        finally:
            # Clean up session after use
            await self._cleanup_session(session)

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
        """Cleanup all sessions on shutdown."""
        # Clean up active forked sessions
        async with self._session_lock:
            for session in self._active_sessions[
                :
            ]:  # Copy list to avoid modification during iteration
                try:
                    await session.disconnect()
                except Exception as e:
                    logger.warning(f"[ClaudeCode] Error disconnecting forked session: {e}")
            self._active_sessions.clear()

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

        logger.info("[ClaudeCode] Cleanup complete (templates and forked sessions)")
