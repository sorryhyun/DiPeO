"""Unified Claude Code Custom client with full system prompt override."""

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
from ..claude_code.transport.session_wrapper import SessionQueryWrapper

logger = logging.getLogger(__name__)

# Session pooling configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"


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

        logger.info(
            f"[ClaudeCodeCustom] Initialized with SESSION_POOL_ENABLED={SESSION_POOL_ENABLED}"
        )

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

    def _extract_tool_result(self, response_text: str) -> dict | None:
        """Extract tool result from Claude Code response."""
        import json

        logger.debug(
            f"[ClaudeCodeCustom] Attempting to extract tool result from response: "
            f"{response_text[:500]}{'...' if len(response_text) > 500 else ''}"
        )

        # Try to parse the entire response as JSON first
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                # Check for 'data' field from our tool responses
                if "data" in data:
                    logger.debug(
                        f"[ClaudeCodeCustom] Found tool result in 'data' field: {data['data']}"
                    )
                    return data["data"]
                # Check for direct structured output
                if "message_ids" in data or "decision" in data:
                    logger.debug(f"[ClaudeCodeCustom] Found direct structured output: {data}")
                    return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[ClaudeCodeCustom] Response is not valid JSON: {e}")

        # Fallback: Look for JSON objects in the text
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.finditer(json_pattern, response_text)
        for match in matches:
            try:
                data = json.loads(match.group(0))
                if "message_ids" in data or "decision" in data:
                    logger.debug(f"[ClaudeCodeCustom] Found tool result in embedded JSON: {data}")
                    return data
            except (json.JSONDecodeError, ValueError):
                continue

        logger.debug("[ClaudeCodeCustom] No tool result found in response")
        return None

    def _parse_response(
        self, response: str, execution_phase: ExecutionPhase | None = None
    ) -> LLMResponse:
        """Parse Claude Code response to unified format."""
        # Extract usage if present in response
        usage = self._extract_usage_from_response(response)

        # Clean response of any metadata patterns
        clean_response = re.sub(
            r"Tokens:\s*input=\d+,\s*output=\d+,\s*total=\d+", "", response
        ).strip()

        # Check if response contains tool usage
        structured_output = None
        tool_result = self._extract_tool_result(response)

        if tool_result:
            # Tool was used, create structured output from tool result
            logger.debug(
                f"[ClaudeCodeCustom] Tool result extracted successfully for {execution_phase}: "
                f"{tool_result}"
            )
            if execution_phase == ExecutionPhase.MEMORY_SELECTION:
                from dipeo.infrastructure.llm.drivers.types import MemorySelectionOutput

                structured_output = MemorySelectionOutput(
                    message_ids=tool_result.get("message_ids", [])
                )
                logger.debug(
                    f"[ClaudeCodeCustom] Created MemorySelectionOutput from tool: "
                    f"selected {len(tool_result.get('message_ids', []))} messages"
                )
            elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
                from dipeo.infrastructure.llm.drivers.types import DecisionOutput

                structured_output = DecisionOutput(decision=tool_result.get("decision", False))
                logger.debug(
                    f"[ClaudeCodeCustom] Created DecisionOutput from tool: "
                    f"decision={tool_result.get('decision', False)}"
                )
        else:
            # Simplified fallback parsing
            logger.warning(
                f"[ClaudeCodeCustom] No tool result found for {execution_phase}, "
                f"falling back to text parsing. Response preview: {clean_response[:200]}..."
            )
            if execution_phase == ExecutionPhase.MEMORY_SELECTION:
                structured_output = self._parse_memory_selection(clean_response)
                logger.debug(
                    f"[ClaudeCodeCustom] Text parsing result: "
                    f"selected {len(structured_output.message_ids) if structured_output else 0} messages"
                )
            elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
                structured_output = self._parse_decision(clean_response)
                logger.debug(
                    f"[ClaudeCodeCustom] Text parsing result: "
                    f"decision={structured_output.decision if structured_output else None}"
                )

        return LLMResponse(
            content=clean_response,
            raw_response=response,
            usage=usage,
            model="claude-code-custom",
            provider=self.provider_type,
            structured_output=structured_output,
        )

    def _parse_memory_selection(self, response: str) -> Any:
        """Parse memory selection from response text."""
        import json

        from dipeo.infrastructure.llm.drivers.types import MemorySelectionOutput

        # Try to parse as JSON array directly
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return MemorySelectionOutput(message_ids=data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Look for JSON array in text
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            try:
                message_ids = json.loads(match.group(0))
                return MemorySelectionOutput(message_ids=message_ids)
            except (json.JSONDecodeError, ValueError):
                pass

        # Default to empty selection
        return MemorySelectionOutput(message_ids=[])

    def _parse_decision(self, response: str) -> Any:
        """Parse decision from response text."""
        from dipeo.infrastructure.llm.drivers.types import DecisionOutput

        response_upper = response.strip().upper()

        # Check for YES/NO at the start
        if response_upper.startswith("YES"):
            return DecisionOutput(decision=True)
        elif response_upper.startswith("NO"):
            return DecisionOutput(decision=False)

        # Check anywhere in response (more lenient)
        if "YES" in response_upper and "NO" not in response_upper:
            return DecisionOutput(decision=True)
        elif "NO" in response_upper and "YES" not in response_upper:
            return DecisionOutput(decision=False)

        # Default to NO for safety
        return DecisionOutput(decision=False)

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
        system_message, message_text = self._prepare_message(messages)

        # Configure MCP server based on execution phase
        mcp_server = None
        use_tools = False

        # Enable tools for structured output phases
        if execution_phase in (ExecutionPhase.MEMORY_SELECTION, ExecutionPhase.DECISION_EVALUATION):
            from ..claude_code.tools import create_dipeo_mcp_server

            mcp_server = create_dipeo_mcp_server()
            use_tools = True
            logger.debug(
                f"[ClaudeCodeCustom] MCP server configured for {execution_phase}: "
                f"tools={'select_memory_messages, make_decision' if execution_phase == ExecutionPhase.MEMORY_SELECTION else 'make_decision'}"
            )

        # Get system prompt based on execution phase
        # CUSTOM BEHAVIOR: Pass the system_message to allow complete override
        person_name = kwargs.get("person_name")
        if not person_name and system_message and "YOUR NAME:" in system_message:
            # Extract person name from system message if not provided in kwargs
            match = re.search(r"YOUR NAME:\s*([^\n]+)", system_message)
            if match:
                person_name = match.group(1).strip()
                # Remove the YOUR NAME line from system message to avoid duplication
                system_message = re.sub(r"YOUR NAME:\s*[^\n]+\n*", "", system_message)

        # CUSTOM: Pass system_message to _get_system_prompt for override behavior
        system_prompt = self._get_system_prompt(
            execution_phase,
            use_tools=use_tools,
            person_name=person_name,
            system_message=system_message,
        )

        # CUSTOM: If we already used the system_message, don't append it again
        # The system_prompt is already the complete override
        if not system_prompt:
            system_prompt = system_message

        # Set up workspace directory for claude-code
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

        # Create Claude Code options with MCP server if configured
        options_dict = {
            "system_prompt": system_prompt,
        }

        # Add MCP server and allowed tools if configured
        if mcp_server:
            options_dict["mcp_servers"] = {"dipeo_structured_output": mcp_server}
            # Add allowed tools with proper MCP naming convention
            options_dict["allowed_tools"] = [
                "mcp__dipeo_structured_output__select_memory_messages",
                "mcp__dipeo_structured_output__make_decision",
            ]
            logger.debug(f"[ClaudeCodeCustom] MCP tools enabled: {options_dict['allowed_tools']}")

        # Add other kwargs (but remove text_format and person_name if present)
        kwargs.pop("text_format", None)  # Remove text_format as we don't use it
        kwargs.pop("person_name", None)  # Remove person_name as it's already used in system prompt
        options_dict.update(kwargs)

        # Create options
        options = ClaudeCodeOptions(**options_dict)

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
                # Collect only the final result from Claude Code SDK
                # Claude Code sends multiple messages: SystemMessage, AssistantMessage, ResultMessage
                # We only want the ResultMessage to avoid duplication
                result_text = ""
                async for message in wrapper.query(message_text):
                    # Only process ResultMessage for the final response
                    if hasattr(message, "result"):
                        # This is the final, authoritative response
                        result_text = str(message.result)
                        break  # We have the result, no need to process further messages
                return self._parse_response(result_text, execution_phase)

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
        system_message, message_text = self._prepare_message(messages)

        # Configure MCP server based on execution phase
        mcp_server = None
        use_tools = False

        # Enable tools for structured output phases
        if execution_phase in (ExecutionPhase.MEMORY_SELECTION, ExecutionPhase.DECISION_EVALUATION):
            from ..claude_code.tools import create_dipeo_mcp_server

            mcp_server = create_dipeo_mcp_server()
            use_tools = True
            logger.debug(
                f"[ClaudeCodeCustom] MCP server configured for {execution_phase}: "
                f"tools={'select_memory_messages, make_decision' if execution_phase == ExecutionPhase.MEMORY_SELECTION else 'make_decision'}"
            )

        # Get system prompt based on execution phase
        # CUSTOM BEHAVIOR: Pass the system_message to allow complete override
        person_name = kwargs.get("person_name")
        if not person_name and system_message and "YOUR NAME:" in system_message:
            # Extract person name from system message if not provided in kwargs
            match = re.search(r"YOUR NAME:\s*([^\n]+)", system_message)
            if match:
                person_name = match.group(1).strip()
                # Remove the YOUR NAME line from system message to avoid duplication
                system_message = re.sub(r"YOUR NAME:\s*[^\n]+\n*", "", system_message)

        # CUSTOM: Pass system_message to _get_system_prompt for override behavior
        system_prompt = self._get_system_prompt(
            execution_phase,
            use_tools=use_tools,
            person_name=person_name,
            system_message=system_message,
        )

        # CUSTOM: If we already used the system_message, don't append it again
        if not system_prompt:
            system_prompt = system_message

        # Set up workspace directory for claude-code
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

        # Create Claude Code options with streaming enabled
        options_dict = {
            "system_prompt": system_prompt,
            "stream": True,  # Enable streaming if supported
        }

        # Add MCP server and allowed tools if configured
        if mcp_server:
            options_dict["mcp_servers"] = {"dipeo_structured_output": mcp_server}
            # Add allowed tools with proper MCP naming convention
            options_dict["allowed_tools"] = [
                "mcp__dipeo_structured_output__select_memory_messages",
                "mcp__dipeo_structured_output__make_decision",
            ]
            logger.debug(f"[ClaudeCodeCustom] MCP tools enabled: {options_dict['allowed_tools']}")

        # Add other kwargs (but remove text_format and person_name if present)
        kwargs.pop("text_format", None)  # Remove text_format as we don't use it
        kwargs.pop("person_name", None)  # Remove person_name as it's already used in system prompt
        options_dict.update(kwargs)

        # Create options
        options = ClaudeCodeOptions(**options_dict)

        # Use QueryClientWrapper with context manager
        async with SessionQueryWrapper(
            options=options, execution_phase=str(execution_phase) if execution_phase else "default"
        ) as wrapper:
            # Stream messages from Claude Code SDK
            # For streaming, we need to handle both AssistantMessage (for real-time streaming)
            # and ResultMessage (for final result)
            has_yielded_content = False
            async for message in wrapper.query(message_text):
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
