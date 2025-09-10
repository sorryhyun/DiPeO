"""Unified Claude Code client that merges adapter and wrapper layers."""

import asyncio
import logging
import os
import re
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
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)

from .prompts import DIRECT_EXECUTION_PROMPT, LLM_DECISION_PROMPT, MEMORY_SELECTION_PROMPT
from .transport.session_wrapper import SessionQueryWrapper

logger = logging.getLogger(__name__)

# Session pooling configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"


class UnifiedClaudeCodeClient:
    """Unified Claude Code client that combines adapter and wrapper functionality."""

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.model = config.model or "claude-code"
        self.provider_type = "claude_code"

        # Set capabilities
        self.capabilities = self._get_capabilities()

        # Initialize retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        logger.info(f"[ClaudeCode] Initialized with SESSION_POOL_ENABLED={SESSION_POOL_ENABLED}")

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Claude Code provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.CLAUDE_CODE,
            max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
            max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
        )

    def _get_system_prompt(self, execution_phase: ExecutionPhase | None = None) -> str | None:
        """Get system prompt based on execution phase."""
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            return MEMORY_SELECTION_PROMPT
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            return LLM_DECISION_PROMPT
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            return DIRECT_EXECUTION_PROMPT
        return None

    def _prepare_message(self, messages: list[Message]) -> str:
        """Prepare messages for Claude Code SDK."""
        # Claude Code SDK expects a single message string
        # Combine all messages into a single prompt
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                formatted_messages.append(f"System: {msg.content}")
            elif msg.role == "assistant":
                formatted_messages.append(f"Assistant: {msg.content}")
            else:  # user role
                formatted_messages.append(f"User: {msg.content}")

        return "\n\n".join(formatted_messages)

    def _extract_usage_from_response(self, response_text: str) -> LLMUsage | None:
        """Extract token usage from response if included."""
        # Claude Code SDK may include usage info in response metadata
        # Look for patterns like "Tokens: input=X, output=Y, total=Z"
        usage_pattern = r"Tokens:\s*input=(\d+),\s*output=(\d+),\s*total=(\d+)"
        match = re.search(usage_pattern, response_text)

        if match:
            return LLMUsage(
                input_tokens=int(match.group(1)),
                output_tokens=int(match.group(2)),
                total_tokens=int(match.group(3)),
            )

        return None

    def _parse_response(self, response: str) -> LLMResponse:
        """Parse Claude Code response to unified format."""
        # Extract usage if present in response
        usage = self._extract_usage_from_response(response)

        # Clean response of any metadata patterns
        clean_response = re.sub(
            r"Tokens:\s*input=\d+,\s*output=\d+,\s*total=\d+", "", response
        ).strip()

        return LLMResponse(
            content=clean_response,
            raw_response=response,
            usage=usage,
            model=self.model,
            provider=self.provider_type,
        )

    async def async_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute async chat completion with retry logic."""
        # Prepare message
        message_text = self._prepare_message(messages)

        # Get system prompt based on execution phase
        system_prompt = self._get_system_prompt(execution_phase)

        # Set up workspace directory for claude-code
        if "cwd" not in kwargs:
            import os
            from pathlib import Path

            trace_id = kwargs.get("trace_id", "default")
            root = os.getenv(
                "DIPEO_CLAUDE_WORKSPACES", os.path.join(os.getcwd(), ".dipeo", "workspaces")
            )
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)

        # Create Claude Code options
        options = ClaudeCodeOptions(
            message=message_text,
            model=model or self.model,
            system_prompt=system_prompt,
            # Claude Code SDK doesn't support these parameters directly
            # but we can include them in kwargs for future compatibility
            **kwargs,
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
                response = await wrapper.query()
                return self._parse_response(response)

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
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        # Prepare message
        message_text = self._prepare_message(messages)

        # Get system prompt based on execution phase
        system_prompt = self._get_system_prompt(execution_phase)

        # Set up workspace directory for claude-code
        if "cwd" not in kwargs:
            import os
            from pathlib import Path

            trace_id = kwargs.get("trace_id", "default")
            root = os.getenv(
                "DIPEO_CLAUDE_WORKSPACES", os.path.join(os.getcwd(), ".dipeo", "workspaces")
            )
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)

        # Create Claude Code options with streaming enabled
        options = ClaudeCodeOptions(
            message=message_text,
            model=model or self.model,
            system_prompt=system_prompt,
            stream=True,  # Enable streaming if supported
            **kwargs,
        )

        # Use QueryClientWrapper with context manager
        async with SessionQueryWrapper(
            options=options, execution_phase=str(execution_phase) if execution_phase else "default"
        ) as wrapper:
            # Note: Claude Code SDK might not support true streaming yet
            # If it doesn't, we can simulate streaming by yielding chunks
            response = await wrapper.query()

            # Simulate streaming by yielding in chunks
            chunk_size = 100  # Adjust as needed
            for i in range(0, len(response), chunk_size):
                yield response[i : i + chunk_size]

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
