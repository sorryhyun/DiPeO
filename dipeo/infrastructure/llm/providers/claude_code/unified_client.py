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

FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})
FORK_SESSION_ENABLED = (
    FORK_SESSION_SUPPORTED and os.getenv("DIPEO_CLAUDE_FORK_SESSION", "true").lower() == "true"
)


class UnifiedClaudeCodeClient:
    """Client with template session forking and context manager lifecycle."""

    def __init__(self, config: AdapterConfig):
        self.config = config

        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        self.provider_type = ConfigProviderType.CLAUDE_CODE
        self.capabilities = self._get_capabilities()

        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        self._parser = ClaudeCodeResponseParser()
        self._processor = ClaudeCodeMessageProcessor()

        # Template sessions for efficiency
        self._template_sessions: dict[str, ClaudeSDKClient | None] = {
            ExecutionPhase.MEMORY_SELECTION.value: None,
            ExecutionPhase.DIRECT_EXECUTION.value: None,
            "default": None,
        }
        self._template_lock = asyncio.Lock()

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.CLAUDE_CODE,
            max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
            max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
        )

    def _setup_workspace(self, kwargs: dict) -> None:
        """Configure workspace directory (modifies kwargs in-place)."""
        if "cwd" not in kwargs:
            from pathlib import Path

            trace_id = kwargs.pop("trace_id", "default")
            root = os.getenv("DIPEO_CLAUDE_WORKSPACES", str(BASE_DIR / ".dipeo" / "workspaces"))
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)
        else:
            kwargs.pop("trace_id", None)

    async def _get_or_create_template(
        self, options: ClaudeAgentOptions, execution_phase: str, trace_id: str = ""
    ) -> ClaudeSDKClient:
        """Get or create template session for phase (created once, reused for forking)."""
        async with self._template_lock:
            if self._template_sessions.get(execution_phase):
                return self._template_sessions[execution_phase]

            if FORK_SESSION_ENABLED:
                options.fork_session = True

            async with atime_phase(
                trace_id,
                "claude_code",
                f"{execution_phase}__template_create",
            ):
                template_session = ClaudeSDKClient(options=options)
                await template_session.connect(None)

            self._template_sessions[execution_phase] = template_session

            return template_session

    async def _get_forked_session_options(
        self, options: ClaudeAgentOptions, execution_phase: str, trace_id: str = ""
    ) -> ClaudeAgentOptions:
        """Get forked session options from template (or original if forking unavailable)."""
        if FORK_SESSION_ENABLED:
            try:
                template = await self._get_or_create_template(options, execution_phase, trace_id)

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

        # Fallback to fresh session
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
        """Execute async chat with template forking and retry logic."""
        trace_id = kwargs.get("trace_id", "")
        phase_key = execution_phase.value if execution_phase else "default"

        async with atime_phase(trace_id, "claude_code", f"{phase_key}__prepare_messages"):
            system_message, formatted_messages = self._processor.prepare_message(messages)

        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        async with atime_phase(trace_id, "claude_code", f"{phase_key}__configure_tools"):
            tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        async with atime_phase(trace_id, "claude_code", f"{phase_key}__build_system_prompt"):
            system_prompt = self._processor.build_system_prompt(
                system_message,
                execution_phase,
                use_tools,
                **kwargs,
            )

        self._setup_workspace(kwargs)

        async with atime_phase(trace_id, "claude_code", f"{phase_key}__build_options"):
            options_dict = self._processor.build_claude_options(
                system_prompt, tool_options, hooks_config, stream=False, **kwargs
            )
            options = ClaudeAgentOptions(**options_dict)
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
            phase_key = execution_phase.value if execution_phase else "default"
            forked_options = await self._get_forked_session_options(options, phase_key, trace_id)

            async def message_generator():
                for msg in formatted_messages:
                    yield msg

            if formatted_messages:
                query_input = message_generator()
            else:
                # Fallback message generator
                async def default_generator():
                    yield {
                        "type": "user",
                        "message": json.dumps({"role": "user", "content": "Please respond"}),
                    }

                query_input = default_generator()

            # Context manager handles connection/disconnection automatically
            session_id = f"{phase_key}_{uuid4()}"
            async with (
                atime_phase(trace_id, "claude_code", f"{phase_key}__api_call"),
                ClaudeSDKClient(options=forked_options) as client,
            ):
                async with atime_phase(trace_id, "claude_code", f"{phase_key}__send"):
                    await client.query(query_input)

                async with atime_phase(trace_id, "claude_code", f"{phase_key}__collect"):
                    result_text, tool_invocation_data = await self._parser.collect_response(
                        client.receive_response()
                    )

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
        """Stream chat completion with template forking."""
        system_message, formatted_messages = self._processor.prepare_message(messages)

        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = self._processor.create_tool_options(execution_phase, use_tools)

        system_prompt = self._processor.build_system_prompt(
            system_message,
            execution_phase,
            use_tools,
            **kwargs,
        )

        self._setup_workspace(kwargs)

        options_dict = self._processor.build_claude_options(
            system_prompt, tool_options, hooks_config, stream=True, **kwargs
        )
        options = ClaudeAgentOptions(**options_dict)

        phase_key = execution_phase.value if execution_phase else "default"
        trace_id = kwargs.get("trace_id", "")
        forked_options = await self._get_forked_session_options(options, phase_key, trace_id)

        async def message_generator():
            for msg in formatted_messages:
                yield msg

        if formatted_messages:
            query_input = message_generator()
        else:
            # Fallback message generator
            async def default_generator():
                yield {
                    "type": "user",
                    "message": json.dumps({"role": "user", "content": "Please respond"}),
                }

            query_input = default_generator()

        # Context manager handles cleanup automatically
        session_id = f"{phase_key}_{uuid4()}"

        async with ClaudeSDKClient(options=forked_options) as client:
            await client.query(query_input, session_id=session_id)

            has_yielded_content = False
            async for message in client.receive_response():
                if hasattr(message, "content") and not hasattr(message, "result"):
                    for block in message.content:
                        # Skip thinking blocks - only stream text
                        block_type = getattr(block, "type", None)
                        if block_type == "thinking":
                            continue
                        if hasattr(block, "text") and block.text:
                            has_yielded_content = True
                            yield block.text
                elif hasattr(message, "result"):
                    if not has_yielded_content:
                        yield str(message.result)
                    # Iterator auto-terminates after ResultMessage

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
        """Execute batch requests (no native batch API, uses asyncio.gather)."""
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
        """Cleanup template sessions (forked sessions auto-cleanup via context manager)."""
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

        # Allow subprocess graceful termination to avoid EPIPE errors
        await asyncio.sleep(0.5)

        logger.info("[ClaudeCode] Cleanup complete (template sessions)")
