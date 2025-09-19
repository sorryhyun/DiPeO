"""Message processing utilities for Claude Code provider.

This module handles message preparation, system prompt generation,
and phase-specific prompt construction for the Claude Code adapter.
"""

import json
import logging
import re
from typing import Any

from dipeo.diagram_generated import Message
from dipeo.diagram_generated.enums import ExecutionPhase

from .prompts import DIRECT_EXECUTION_PROMPT, LLM_DECISION_PROMPT, MEMORY_SELECTION_PROMPT

logger = logging.getLogger(__name__)


class ClaudeCodeMessageProcessor:
    """Processor for Claude Code messages and prompts."""

    @staticmethod
    def get_system_prompt(
        execution_phase: ExecutionPhase | None = None,
        use_tools: bool = False,
        person_name: str | None = None,
    ) -> str | None:
        """Get appropriate system prompt based on execution phase.

        Args:
            execution_phase: Current execution phase
            use_tools: Whether to include tool usage instructions
            person_name: Name of the person for personalization

        Returns:
            System prompt string or None
        """
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            base_prompt = MEMORY_SELECTION_PROMPT
            # Replace assistant name placeholder if present
            if person_name:
                base_prompt = base_prompt.replace("{assistant_name}", person_name)
            else:
                base_prompt = base_prompt.replace("{assistant_name}", "Assistant")

            if use_tools:
                # Add more specific tool instruction for memory selection
                base_prompt += "\n\nIMPORTANT: Use the select_memory_messages tool to return your selection. Pass the list of message IDs as the message_ids parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            base_prompt = LLM_DECISION_PROMPT
            if use_tools:
                # Add more specific tool instruction
                base_prompt += "\n\nIMPORTANT: Use the make_decision tool to return your decision. Pass true for YES or false for NO as the decision parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            return DIRECT_EXECUTION_PROMPT
        return None

    @staticmethod
    def prepare_message(messages: list[Message]) -> tuple[str | None, str]:
        """Prepare messages for Claude Code format.

        Claude Code SDK expects a serialized message list. System messages
        are aggregated separately so the caller can combine them with a
        phase-specific system prompt.

        Args:
            messages: List of messages to prepare

        Returns:
            Tuple of (system_message, serialized_messages)
        """
        system_messages: list[str] = []
        formatted_messages: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                raw_content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "user")
                raw_content = getattr(msg, "content", "")

            if role == "system":
                system_messages.append(str(raw_content))
                continue

            if isinstance(raw_content, dict):
                content = raw_content
            else:
                content = {
                    "role": role,
                    "content": [{"type": "text", "text": str(raw_content)}],
                }

            if role == "assistant":
                formatted_messages.append({"type": "assistant", "message": content})
            else:
                formatted_messages.append({"type": "user", "message": content})

        system_message = "\n".join(system_messages) if system_messages else None
        serialized_messages = json.dumps(formatted_messages) if formatted_messages else ""

        return system_message, serialized_messages

    @staticmethod
    def create_tool_options(
        execution_phase: ExecutionPhase | None = None,
        tools_enabled: bool = True,
    ) -> dict[str, Any]:
        """Create tool-specific options for Claude Code.

        Args:
            execution_phase: Current execution phase
            tools_enabled: Whether tools are enabled

        Returns:
            Dictionary with tool configuration
        """
        options = {}

        if not tools_enabled or not execution_phase:
            return options

        # Configure MCP server and tools based on phase
        if execution_phase in [ExecutionPhase.MEMORY_SELECTION, ExecutionPhase.DECISION_EVALUATION]:
            from .tools import create_dipeo_mcp_server

            mcp_server = create_dipeo_mcp_server()

            # Determine which tool to use based on phase
            if execution_phase == ExecutionPhase.MEMORY_SELECTION:
                tool_name = "select_memory_messages"
            else:  # DECISION_EVALUATION
                tool_name = "make_decision"

            logger.debug(
                f"[ClaudeCode] MCP server configured for {execution_phase}: tools={tool_name}"
            )

            options["mcp_server"] = mcp_server
            options["allowed_tools"] = [
                "mcp__dipeo_structured_output__select_memory_messages",
                "mcp__dipeo_structured_output__make_decision",
            ]

        return options

    @staticmethod
    def format_hooks_config(hooks_config: dict[str, list[dict]] | None) -> dict[str, Any]:
        """Format hooks configuration for Claude Code SDK.

        Args:
            hooks_config: Raw hooks configuration

        Returns:
            Formatted hooks dictionary for Claude Code SDK
        """
        if not hooks_config:
            return {}

        from claude_code_sdk.types import HookMatcher

        hooks_dict = {}
        for event_type, matchers_list in hooks_config.items():
            event_matchers = []
            for matcher_config in matchers_list:
                hook_matcher = HookMatcher(
                    matcher=matcher_config.get("matcher"), hooks=matcher_config.get("hooks", [])
                )
                event_matchers.append(hook_matcher)

            hooks_dict[event_type] = event_matchers

        logger.debug(f"[ClaudeCode] Configured hooks: {list(hooks_dict.keys())}")
        return {"hooks": hooks_dict}

    @staticmethod
    def build_system_prompt(
        system_message: str | None,
        execution_phase: ExecutionPhase | None,
        use_tools: bool,
        **kwargs,
    ) -> str | None:
        """Combine phase-specific prompt with existing system messaging.

        This mirrors the legacy logic from the unified client but keeps the
        prompt construction responsibilities inside the processor module.
        """
        person_name = kwargs.get("person_name")
        message_body = system_message

        if not person_name and system_message and "YOUR NAME:" in system_message:
            match = re.search(r"YOUR NAME:\s*([^\n]+)", system_message)
            if match:
                person_name = match.group(1).strip()
                message_body = re.sub(r"YOUR NAME:\s*[^\n]+\n*", "", system_message)

        base_prompt = ClaudeCodeMessageProcessor.get_system_prompt(
            execution_phase=execution_phase,
            use_tools=use_tools,
            person_name=person_name,
        )

        if base_prompt and message_body:
            return f"{base_prompt}\n\n{message_body.strip()}".strip()

        return base_prompt or (message_body.strip() if message_body else None)
