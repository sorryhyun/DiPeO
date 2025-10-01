"""Unified Claude Code Custom client with full system prompt override."""

import asyncio
import logging
import os
import re
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from claude_code_sdk import ClaudeAgentOptions, ClaudeSDKClient
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
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)

from ..claude_code.prompts import (
    DIRECT_EXECUTION_PROMPT,
    LLM_DECISION_PROMPT,
    MEMORY_SELECTION_PROMPT,
)

logger = get_module_logger(__name__)

# Check if fork_session is supported
FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})
FORK_SESSION_ENABLED = FORK_SESSION_SUPPORTED and os.getenv("DIPEO_CLAUDE_FORK_SESSION", "true").lower() == "true"

logger.info(f"[ClaudeCodeCustom] Fork session supported: {FORK_SESSION_SUPPORTED}, enabled: {FORK_SESSION_ENABLED}")

class UnifiedClaudeCodeCustomClient:
    """Unified Claude Code Custom client with full system prompt override support.

    This variant allows complete system prompt override, similar to how other
    adapters (like OpenAI/ChatGPT) handle system prompts. When a system_prompt
    is provided from the diagram, it completely replaces any default prompts.
    """

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.provider_type = "claude_code_custom"

        # Set capabilities
        self.capabilities = self._get_capabilities()

        # Initialize retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        # Template sessions for each execution phase (lazy-loaded)
        self._templates: dict[str, ClaudeSDKClient] = {}
        self._template_lock = asyncio.Lock()

        logger.info("[ClaudeCodeCustom] Initialized with simplified template management")

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Claude Code provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.CLAUDE_CODE,
            max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
            max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
        )

    def _get_system_prompt(
        self, execution_phase: ExecutionPhase | None = None, use_tools: bool = False, **kwargs
    ) -> str | None:
        """Get system prompt based on execution phase.

        CUSTOM BEHAVIOR: This method completely overrides the system prompt
        rather than appending to it. If a system_prompt is provided in messages,
        it takes precedence over all phase-specific prompts.
        """
        # Check if a custom system prompt is already provided
        system_message = kwargs.get("system_message", "")
        if system_message:
            # Custom system prompt provided - use it directly, no appending
            logger.debug("[ClaudeCodeCustom] Using custom system prompt (overriding defaults)")
            return system_message

        # No custom system prompt - use phase-specific defaults
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            # Get person name from kwargs if available
            person_name = kwargs.get("person_name")
            # Replace the placeholder in the prompt if person_name is provided
            if person_name:
                base_prompt = MEMORY_SELECTION_PROMPT.format(assistant_name=person_name)
            else:
                # If no person_name, use the prompt without formatting (will show placeholder)
                base_prompt = MEMORY_SELECTION_PROMPT.replace("{assistant_name}", "Assistant")
            if use_tools:
                # Add tool usage instruction
                base_prompt += "\n\nIMPORTANT: Use the select_memory_messages tool to return your selection. Pass the list of message IDs as the message_ids parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            base_prompt = LLM_DECISION_PROMPT
            if use_tools:
                # Add tool usage instruction
                base_prompt += "\n\nIMPORTANT: Use the make_decision tool to return your decision. Pass true for YES or false for NO as the decision parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            return DIRECT_EXECUTION_PROMPT
        return None

    def _prepare_message(self, messages: list[Message]):
        """Prepare messages for Claude Code SDK."""
        # Claude Code SDK expects a single message string
        # Combine all messages into a single prompt
        formatted_messages = []
        system_message = ""

        for msg in messages:
            # Handle both dict and Message object formats
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = msg.role
                content = {"role": msg.role, "content": [{"type": "text", "text": msg.content}]}

            if role == "system":
                system_message = content
            elif role == "assistant":
                formatted_messages.append({"type": "assistant", "message": content})
            else:  # user role
                formatted_messages.append({"type": "user", "message": content})

        return system_message, str(formatted_messages)

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

    def _create_tool_options(
        self, execution_phase: ExecutionPhase | None = None, use_tools: bool = False
    ) -> dict[str, Any]:
        """Create MCP server configuration for tools based on execution phase."""
        if not use_tools:
            return {}

        # Import the DiPeO MCP server module
        from dipeo.infrastructure.mcp import dipeo_structured_output_server

        tool_options = {
            "mcp_servers": {
                "dipeo_structured_output": {
                    "module": dipeo_structured_output_server,
                    "args": {"output_type": execution_phase.value if execution_phase else "default"},
                }
            },
            "allowed_tools": ["mcp__dipeo_structured_output__*"],
        }

        logger.debug(
            f"[ClaudeCodeCustom] Created MCP server configuration for phase {execution_phase}, "
            f"allowed tools: {tool_options.get('allowed_tools', [])}"
        )
        return tool_options

    def _build_claude_options(
        self, system_prompt, tool_options, hooks_config, stream=False, **kwargs
    ) -> dict[str, Any]:
        """Build options dictionary for ClaudeAgentOptions."""
        options_dict = {"system_prompt": system_prompt, **tool_options, "stream": stream}
        # Add any additional kwargs passed from the configuration
        if "cwd" in kwargs:
            options_dict["cwd"] = kwargs["cwd"]
        if hooks_config:
            options_dict["hooks"] = hooks_config
        return options_dict

    def _parse_response(
        self, response: str, execution_phase: ExecutionPhase | None = None
    ) -> LLMResponse:
        """Parse response from Claude Code SDK."""
        # Extract usage if present
        usage = self._extract_usage_from_response(response)

        # For MEMORY_SELECTION phase, parse the selected message IDs
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            # Look for JSON array pattern [1, 2, 3] or numbered list
            import json

            # Try to parse as JSON array first
            json_pattern = r"\[[\d,\s]+\]"
            match = re.search(json_pattern, response)
            if match:
                try:
                    selected_ids = json.loads(match.group())
                    return LLMResponse(
                        content=str(selected_ids), selected_ids=selected_ids, usage=usage
                    )
                except json.JSONDecodeError:
                    pass

            # Fall back to extracting numbers from the response
            numbers = re.findall(r"\b\d+\b", response)
            if numbers:
                selected_ids = [int(n) for n in numbers]
                return LLMResponse(content=response, selected_ids=selected_ids, usage=usage)

        # For DECISION_EVALUATION phase, extract boolean decision
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            # Look for YES/NO, true/false, or similar patterns
            response_lower = response.lower()
            if any(word in response_lower for word in ["yes", "true", "correct", "affirmative"]):
                decision = True
            elif any(word in response_lower for word in ["no", "false", "incorrect", "negative"]):
                decision = False
            else:
                # Default to False if unclear
                decision = False

            return LLMResponse(content=response, decision=decision, usage=usage)

        # Default response parsing
        return LLMResponse(content=response, usage=usage)

    def _parse_response_with_tool_data(
        self, tool_data: dict, execution_phase: ExecutionPhase | None = None
    ) -> LLMResponse:
        """Parse response when MCP tool was invoked (structured output)."""
        # When using MCP tools, the tool input IS the structured output
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            # Tool data should contain message_ids
            selected_ids = tool_data.get("message_ids", [])
            return LLMResponse(content=str(selected_ids), selected_ids=selected_ids)
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            # Tool data should contain decision
            decision = tool_data.get("decision", False)
            return LLMResponse(content=str(decision), decision=decision)

        # Default: return tool data as is
        return LLMResponse(content=str(tool_data))

    async def _get_or_create_template(
        self,
        options: ClaudeAgentOptions,
        execution_phase: str
    ) -> ClaudeSDKClient:
        """Get or create a template session for the given execution phase.

        Templates are pre-created and reused for efficiency, with fork_session
        ensuring clean state for each actual query.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier

        Returns:
            Template ClaudeSDKClient ready for forking
        """
        async with self._template_lock:
            # Check if template already exists and is connected
            if execution_phase in self._templates:
                template = self._templates[execution_phase]
                # Return existing template
                logger.debug(f"[ClaudeCodeCustom] Reusing template for phase '{execution_phase}'")
                return template

            # Create new template session
            logger.info(f"[ClaudeCodeCustom] Creating template session for phase '{execution_phase}'")

            # Enable fork_session if supported
            if FORK_SESSION_ENABLED:
                options.fork_session = True
                logger.debug(f"[ClaudeCodeCustom] Enabled fork_session for phase '{execution_phase}'")

            # Create and connect template
            template = ClaudeSDKClient(options=options)
            await template.connect(None)

            # Store template for reuse
            self._templates[execution_phase] = template

            return template

    async def _execute_query(
        self,
        template: ClaudeSDKClient,
        query_input: str,
        execution_phase: ExecutionPhase | None,
        session_id: str
    ) -> LLMResponse:
        """Execute a query on a template session.

        When fork_session is enabled, this creates a fresh forked session
        automatically for clean state isolation.

        Args:
            template: Template client to query
            query_input: The prompt to send
            execution_phase: Execution phase for response parsing
            session_id: Unique session ID for this query

        Returns:
            Parsed LLM response
        """
        # Send query with unique session ID (triggers fork if enabled)
        await template.query(query_input, session_id=session_id)

        # Collect response
        result_text = ""
        tool_invocation_data = None

        async for message in template.receive_messages():
            # Check for tool invocations
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

            # Process ResultMessage
            if hasattr(message, "result"):
                result_text = str(message.result)
                # Log if session was forked
                if hasattr(message, "session_id") and message.session_id != session_id:
                    logger.debug(
                        f"[ClaudeCodeCustom] Session forked from {session_id} to {message.session_id}"
                    )
                break

        # Parse response
        if tool_invocation_data:
            logger.debug(
                f"[ClaudeCodeCustom] Using tool invocation data as response for {execution_phase}: "
                f"{tool_invocation_data}"
            )
            parsed = self._parse_response_with_tool_data(tool_invocation_data, execution_phase)
            parsed.provider = self.provider_type
            parsed.raw_response = str(tool_invocation_data)
            return parsed

        parsed = self._parse_response(result_text, execution_phase)
        parsed.provider = self.provider_type
        parsed.raw_response = result_text
        return parsed

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
        system_message, formatted_messages = self._prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = self._create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase (with custom override support)
        system_prompt = self._get_system_prompt(
            execution_phase, use_tools, system_message=system_message
        )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options
        options_dict = self._build_claude_options(
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
            # Get or create template for this execution phase
            phase_key = str(execution_phase) if execution_phase else "default"
            template = await self._get_or_create_template(options, phase_key)

            # Execute query with unique session ID (triggers fork if enabled)
            session_id = f"{phase_key}_{uuid4()}"
            return await self._execute_query(template, formatted_messages, execution_phase, session_id)

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
        system_message, formatted_messages = self._prepare_message(messages)

        # Configure MCP server based on execution phase
        use_tools = execution_phase in (
            ExecutionPhase.MEMORY_SELECTION,
            ExecutionPhase.DECISION_EVALUATION,
        )
        tool_options = self._create_tool_options(execution_phase, use_tools)

        # Get system prompt based on execution phase (with custom override support)
        system_prompt = self._get_system_prompt(
            execution_phase, use_tools, system_message=system_message
        )

        # Set up workspace directory for claude-code
        self._setup_workspace(kwargs)

        # Create Claude Code options with streaming
        options_dict = self._build_claude_options(
            system_prompt, tool_options, hooks_config, stream=True, **kwargs
        )
        options = ClaudeAgentOptions(**options_dict)

        # Get or create template for this execution phase
        phase_key = str(execution_phase) if execution_phase else "default"
        template = await self._get_or_create_template(options, phase_key)

        # Execute query with unique session ID (triggers fork if enabled)
        session_id = f"{phase_key}_{uuid4()}"
        await template.query(formatted_messages, session_id=session_id)

        # Stream responses
        has_yielded_content = False
        async for message in template.receive_messages():
            if hasattr(message, "content") and not hasattr(message, "result"):
                # Stream content from AssistantMessage
                for block in message.content:
                    if hasattr(block, "text") and block.text:
                        has_yielded_content = True
                        yield block.text
            elif hasattr(message, "result"):
                # If we haven't yielded any content yet, yield the result
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

    async def cleanup(self) -> None:
        """Cleanup template sessions on shutdown."""
        async with self._template_lock:
            for phase, template in self._templates.items():
                try:
                    await template.disconnect()
                    logger.debug(f"[ClaudeCodeCustom] Disconnected template for phase '{phase}'")
                except Exception as e:
                    logger.warning(f"[ClaudeCodeCustom] Error disconnecting template '{phase}': {e}")
            self._templates.clear()
        logger.info("[ClaudeCodeCustom] Cleanup complete")