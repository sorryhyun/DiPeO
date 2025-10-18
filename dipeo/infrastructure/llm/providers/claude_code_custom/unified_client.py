"""Unified Claude Code Custom client with full system prompt override."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from claude_agent_sdk import ClaudeAgentOptions
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
)

from ..claude_code.message_processor import ClaudeCodeMessageProcessor
from .config import FORK_SESSION_ENABLED, get_capabilities
from .options_builder import OptionsBuilder
from .response_parser import ResponseParser
from .session_manager import SessionManager

logger = get_module_logger(__name__)


class UnifiedClaudeCodeCustomClient:
    """Unified Claude Code Custom client with full system prompt override support.

    This variant allows complete system prompt override, similar to how other
    adapters (like OpenAI/ChatGPT) handle system prompts. When a system_prompt
    is provided from the diagram, it completely replaces any default prompts.
    Uses template-based session management with forking for efficiency.
    """

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.provider_type = "claude_code_custom"
        self.capabilities = get_capabilities()

        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        self.session_manager = SessionManager()

        logger.info(
            "[ClaudeCodeCustom] Initialized with template-based session management (fork enabled: %s)",
            FORK_SESSION_ENABLED,
        )

    async def _execute_query(
        self,
        session,
        query_input: str,
        execution_phase: ExecutionPhase | None,
        session_id: str,
    ) -> LLMResponse:
        """Execute a query on a session."""
        try:
            await session.query(query_input, session_id=session_id)

            result_text = ""
            tool_invocation_data = None

            async for message in session.receive_response():
                if hasattr(message, "content") and not hasattr(message, "result"):
                    for block in message.content:
                        if hasattr(block, "name") and hasattr(block, "input"):
                            if block.name.startswith("mcp__dipeo_structured_output__"):
                                logger.debug(
                                    f"[ClaudeCodeCustom] Found MCP tool invocation: {block.name} "
                                    f"with input: {block.input}"
                                )
                                tool_invocation_data = block.input
                                break

                if hasattr(message, "result"):
                    result_text = str(message.result)
                    if hasattr(message, "session_id") and message.session_id != session_id:
                        logger.debug(
                            f"[ClaudeCodeCustom] Session forked from {session_id} to {message.session_id}"
                        )

            if tool_invocation_data:
                logger.debug(
                    f"[ClaudeCodeCustom] Using tool invocation data as response for {execution_phase}: "
                    f"{tool_invocation_data}"
                )
                parsed = ResponseParser.parse_response_with_tool_data(
                    tool_invocation_data, execution_phase
                )
                parsed.provider = self.provider_type
                parsed.raw_response = str(tool_invocation_data)
                return parsed

            parsed = ResponseParser.parse_response(result_text, execution_phase)
            parsed.provider = self.provider_type
            parsed.raw_response = result_text
            return parsed
        finally:
            await self.session_manager.cleanup_session(session)

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
        system_message, formatted_messages = ClaudeCodeMessageProcessor.prepare_message(messages)

        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = OptionsBuilder.create_tool_options(execution_phase, use_tools)

        system_prompt = OptionsBuilder.get_system_prompt(
            execution_phase, use_tools, system_message=system_message, **kwargs
        )

        OptionsBuilder.setup_workspace(kwargs)

        options_dict = OptionsBuilder.build_claude_options(
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
            phase_key = str(execution_phase) if execution_phase else "default"
            session = await self.session_manager.create_forked_session(options, phase_key)
            session_id = f"{phase_key}_{uuid4()}"
            return await self._execute_query(
                session, formatted_messages, execution_phase, session_id
            )

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
        """Stream chat completion response."""
        system_message, formatted_messages = ClaudeCodeMessageProcessor.prepare_message(messages)

        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = OptionsBuilder.create_tool_options(execution_phase, use_tools)

        system_prompt = OptionsBuilder.get_system_prompt(
            execution_phase, use_tools, system_message=system_message, **kwargs
        )

        OptionsBuilder.setup_workspace(kwargs)

        options_dict = OptionsBuilder.build_claude_options(
            system_prompt, tool_options, hooks_config, stream=True, **kwargs
        )
        options = ClaudeAgentOptions(**options_dict)

        phase_key = str(execution_phase) if execution_phase else "default"
        session = await self.session_manager.create_forked_session(options, phase_key)

        try:
            session_id = f"{phase_key}_{uuid4()}"
            await session.query(formatted_messages, session_id=session_id)

            has_yielded_content = False
            async for message in session.receive_response():
                if hasattr(message, "content") and not hasattr(message, "result"):
                    for block in message.content:
                        if hasattr(block, "text") and block.text:
                            has_yielded_content = True
                            yield block.text
                elif hasattr(message, "result"):
                    if not has_yielded_content:
                        yield str(message.result)
        finally:
            await self.session_manager.cleanup_session(session)

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
        await self.session_manager.cleanup_all()
