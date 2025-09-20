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
    def prepare_message(messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
        """Prepare messages for Claude Code format.

        Returns a tuple of system prompt text and a list of formatted
        messages expected by the Claude Code SDK.
        """
        system_messages: list[str] = []
        formatted_messages: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role")
                raw_content = msg.get("content", "")
                message_type = msg.get("message_type")
            else:
                role = getattr(msg, "role", None)
                raw_content = getattr(msg, "content", "")
                message_type = getattr(msg, "message_type", None)

            if not role:
                if message_type == "system_to_person":
                    role = "system"
                elif message_type == "person_to_system":
                    role = "user"
                elif message_type == "person_to_person":
                    role = "assistant"
                else:
                    role = "user"

            if role == "system":
                system_messages.append(str(raw_content).strip() if raw_content else "")
                continue

            message_payload = {
                "role": role,
                "content": ClaudeCodeMessageProcessor._build_sdk_content(raw_content),
            }

            if role == "assistant":
                formatted_messages.append({"type": "assistant", "message": message_payload})
            else:
                formatted_messages.append({"type": "user", "message": message_payload})

        system_message = "\n".join([msg for msg in system_messages if msg]) or None

        if not formatted_messages:
            fallback_text = system_message or "Please respond"
            formatted_messages.append(
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": ClaudeCodeMessageProcessor._build_sdk_content(fallback_text),
                    },
                }
            )

        return system_message, formatted_messages

    @staticmethod
    def _build_sdk_content(raw_content: Any) -> list[dict[str, Any]]:
        """Convert message content into Claude SDK block format."""
        if isinstance(raw_content, list):
            # Only flatten if all items are content blocks (have 'type' field)
            # This prevents flattening of separate messages into a single content array
            if all(isinstance(item, dict) and item.get("type") for item in raw_content):
                return raw_content  # Already in proper block format
            elif all(isinstance(item, dict) and not item.get("type") for item in raw_content):
                # Convert plain dicts to text blocks
                blocks = []
                for item in raw_content:
                    if "text" in item:
                        blocks.append({"type": "text", "text": str(item["text"])})
                    else:
                        blocks.append({"type": "text", "text": str(item)})
                return blocks
            else:
                # Mixed types - don't flatten, treat as single text content
                return [{"type": "text", "text": str(raw_content)}]

        if isinstance(raw_content, dict):
            if raw_content.get("type"):
                return [raw_content]
            if "content" in raw_content and isinstance(raw_content["content"], list):
                return ClaudeCodeMessageProcessor._build_sdk_content(raw_content["content"])

        return [{"type": "text", "text": str(raw_content)}]

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

            logger.debug(
                f"[ClaudeCode] MCP server configured for {execution_phase}: select_memory_messages/make_decision"
            )

            options["mcp_servers"] = {"dipeo_structured_output": mcp_server}
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

    @staticmethod
    def build_claude_options(
        system_prompt: str | None,
        tool_options: dict,
        hooks_config: dict | None,
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Build Claude Code options dictionary.

        Args:
            system_prompt: System prompt for Claude
            tool_options: Tool configuration including MCP servers
            hooks_config: Hook configuration for Claude Code SDK
            stream: Whether to enable streaming
            **kwargs: Additional options to pass through

        Returns:
            Dictionary with Claude Code options ready for ClaudeCodeOptions
        """
        options_dict = {
            "system_prompt": system_prompt,
        }

        # Add streaming flag if specified
        if stream:
            options_dict["stream"] = True

        # Add MCP server and allowed tools if configured
        if "mcp_servers" in tool_options:
            options_dict["mcp_servers"] = tool_options["mcp_servers"]
            options_dict["allowed_tools"] = tool_options.get("allowed_tools", [])

        # Add hook configuration if provided
        if hooks_config:
            hooks_dict = ClaudeCodeMessageProcessor.format_hooks_config(hooks_config)
            options_dict.update(hooks_dict)

        # Add other kwargs (but remove text_format and person_name if present)
        kwargs.pop("text_format", None)  # Remove text_format as we don't use it
        kwargs.pop("person_name", None)  # Remove person_name as it's already used in system prompt
        options_dict.update(kwargs)

        return options_dict
