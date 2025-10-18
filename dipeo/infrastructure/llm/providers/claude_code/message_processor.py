"""Message processing utilities for Claude Code provider.

This module handles message preparation, system prompt generation,
and phase-specific prompt construction for the Claude Code adapter.
"""

import json
import logging
import re
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Message
from dipeo.diagram_generated.enums import ExecutionPhase

from .prompts import DIRECT_EXECUTION_PROMPT, LLM_DECISION_PROMPT, MEMORY_SELECTION_PROMPT

logger = get_module_logger(__name__)


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
        messages expected by the Claude Code SDK. Each formatted message
        is a dictionary containing the message type and a JSON string
        payload so the SDK never receives raw Python objects.
        """
        system_messages: list[str] = []
        formatted_messages: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role")
                raw_content = msg.get("content", "")
                message_type = msg.get("message_type")

                # Memory selector may provide nested message objects under the
                # "message" key. Use them as the authoritative source when
                # present so we can convert them into Claude-friendly strings.
                if (not raw_content or raw_content == "") and "message" in msg:
                    nested = msg["message"]
                    if isinstance(nested, dict):
                        role = role or nested.get("role")
                        raw_content = nested.get("content", raw_content)
                    else:
                        role = role or getattr(nested, "role", None)
                        raw_content = getattr(nested, "content", raw_content)
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
                system_messages.append(
                    ClaudeCodeMessageProcessor._stringify_content(raw_content).strip()
                    if raw_content
                    else ""
                )
                continue

            message_payload = {
                "role": role,
                "content": ClaudeCodeMessageProcessor._build_sdk_content(raw_content),
            }

            if role == "assistant":
                formatted_messages.append(
                    {
                        "type": "assistant",
                        "message": message_payload,
                    }
                )
            else:
                formatted_messages.append(
                    {
                        "type": "user",
                        "message": message_payload,
                    }
                )

        system_message = "\n".join([msg for msg in system_messages if msg]) or None

        if not formatted_messages:
            fallback_text = system_message or "Please respond"
            fallback_payload = {
                "role": "user",
                "content": ClaudeCodeMessageProcessor._build_sdk_content(fallback_text),
            }
            formatted_messages.append(
                {
                    "type": "user",
                    "message": fallback_payload,
                }
            )

        # Claude Code SDK doesn't support assistant messages in input,
        # so we convert them to user messages with context prefix instead
        formatted_messages = ClaudeCodeMessageProcessor._convert_assistant_to_user_context(
            formatted_messages
        )

        # Combine consecutive user messages to avoid streaming issues
        formatted_messages = ClaudeCodeMessageProcessor._combine_consecutive_user_messages(
            formatted_messages
        )

        return system_message, formatted_messages

    @staticmethod
    def _convert_assistant_to_user_context(
        formatted_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert assistant messages to user context messages for Claude Code.

        Claude Code SDK only accepts user messages as input. Assistant messages
        (typically from memory) are converted to user messages with a context prefix.

        Args:
            formatted_messages: List of formatted message dictionaries

        Returns:
            Transformed message list with all assistant messages converted to user context
        """
        result = []
        for msg in formatted_messages:
            if msg.get("type") == "assistant":
                # Extract content from assistant message
                msg_data = msg["message"]
                if isinstance(msg_data, str):
                    msg_data = json.loads(msg_data)

                content = msg_data.get("content", [])

                # Convert to user message with context prefix
                text_content = []
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_content.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_content.append(block)
                else:
                    text_content.append(str(content))

                if text_content:
                    context_text = "[Previous response] " + " ".join(text_content)
                    result.append(
                        {
                            "type": "user",
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": context_text}],
                            },
                        }
                    )
            else:
                result.append(msg)

        return result

    @staticmethod
    def _combine_consecutive_user_messages(
        formatted_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Combine consecutive user messages into a single message.

        When multiple messages are retrieved by memory selectors, they should be
        combined into a single message to ensure Claude responds to the whole
        conversation context, not just the last message.

        Args:
            formatted_messages: List of formatted message dictionaries

        Returns:
            List with consecutive user messages combined
        """
        if not formatted_messages:
            return formatted_messages

        result = []
        current_user_messages = []

        for msg in formatted_messages:
            if msg.get("type") == "user":
                # Accumulate consecutive user messages
                current_user_messages.append(msg)
            else:
                # Non-user message encountered, flush accumulated user messages
                if current_user_messages:
                    result.append(
                        ClaudeCodeMessageProcessor._merge_user_messages(current_user_messages)
                    )
                    current_user_messages = []
                result.append(msg)

        # Flush any remaining user messages
        if current_user_messages:
            result.append(ClaudeCodeMessageProcessor._merge_user_messages(current_user_messages))

        return result

    @staticmethod
    def _merge_user_messages(user_messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple user messages into a single message with combined content.

        Args:
            user_messages: List of user message dictionaries

        Returns:
            Single merged user message
        """
        if len(user_messages) == 1:
            return user_messages[0]

        # Combine all content blocks from all messages
        combined_content = []
        for msg in user_messages:
            msg_data = msg["message"]
            if isinstance(msg_data, str):
                msg_data = json.loads(msg_data)

            content = msg_data.get("content", [])
            if isinstance(content, list):
                combined_content.extend(content)
            else:
                # Convert non-list content to text block
                combined_content.append({"type": "text", "text": str(content)})

        return {"type": "user", "message": {"role": "user", "content": combined_content}}

    @staticmethod
    def _transform_assistant_memories_to_tool_result(
        formatted_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Transform assistant-role memory messages to tool_result pattern.

        Claude Code has limitations with assistant-role messages in conversation history.
        This method converts consecutive assistant messages (typically selected memories)
        into a tool_use + tool_result pattern, making them appear as retrieved context
        rather than conversation history.

        The transformation:
        - Detects consecutive assistant messages (excluding the final one)
        - Groups them as memories
        - Creates assistant message with tool_use block (memory_tool)
        - Creates user message with tool_result block containing memory content

        Args:
            formatted_messages: List of formatted message dictionaries

        Returns:
            Transformed message list with memories as tool_result
        """
        if len(formatted_messages) <= 1:
            return formatted_messages

        # Find assistant message indices (exclude the last message which is the actual prompt)
        assistant_indices = []
        for i in range(len(formatted_messages) - 1):  # Exclude last message
            if formatted_messages[i].get("type") == "assistant":
                assistant_indices.append(i)

        # If no assistant messages found, return as-is
        if not assistant_indices:
            return formatted_messages

        # Build result, transforming consecutive assistant blocks
        result = []
        i = 0
        while i < len(formatted_messages):
            # If not an assistant message or it's the last message, keep as-is
            if i not in assistant_indices:
                result.append(formatted_messages[i])
                i += 1
                continue

            # Collect consecutive assistant messages
            memory_messages = []
            start_idx = i
            while i < len(formatted_messages) - 1 and i in assistant_indices:
                memory_messages.append(formatted_messages[i])
                i += 1

            # Transform collected memories to tool_use + tool_result
            if memory_messages:
                # Generate unique tool_use_id
                tool_use_id = f"memory_{abs(hash(str(start_idx)))}"

                # Create tool_use message (assistant)
                tool_use_message = {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": "memory_tool",
                                "input": {},
                            }
                        ],
                    },
                }
                result.append(tool_use_message)

                # Extract and format memory content
                memory_texts = []
                for msg_dict in memory_messages:
                    try:
                        # Message is now a dict, not a JSON string
                        msg_data = msg_dict["message"]
                        if isinstance(msg_data, str):
                            # Fallback: if it's still a JSON string, parse it
                            msg_data = json.loads(msg_data)

                        content = msg_data.get("content", "")

                        # Handle content blocks
                        if isinstance(content, list):
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif isinstance(block, str):
                                    text_parts.append(block)
                            content = " ".join(text_parts) if text_parts else str(content)

                        if content:
                            memory_texts.append(str(content))
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        # If parsing fails, skip this message
                        logger.warning(f"Failed to parse memory message: {msg_dict}, error: {e}")
                        continue

                # Create tool_result message (user)
                memory_content = (
                    "\n\n---\n\n".join(memory_texts) if memory_texts else "No memory content"
                )
                tool_result_message = {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": memory_content,
                            }
                        ],
                    },
                }
                result.append(tool_result_message)

                logger.debug(
                    f"[ClaudeCode] Transformed {len(memory_messages)} assistant messages "
                    f"to tool_result with {len(memory_texts)} memory items"
                )

        return result

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
                        blocks.append(
                            {
                                "type": "text",
                                "text": ClaudeCodeMessageProcessor._stringify_content(item["text"]),
                            }
                        )
                    else:
                        blocks.append(
                            {
                                "type": "text",
                                "text": ClaudeCodeMessageProcessor._stringify_content(item),
                            }
                        )
                return blocks
            else:
                # Mixed types - don't flatten, treat as single text content
                return [
                    {
                        "type": "text",
                        "text": ClaudeCodeMessageProcessor._stringify_content(raw_content),
                    }
                ]

        if isinstance(raw_content, dict):
            if raw_content.get("type"):
                return [raw_content]
            if "content" in raw_content and isinstance(raw_content["content"], list):
                return ClaudeCodeMessageProcessor._build_sdk_content(raw_content["content"])

        return [
            {
                "type": "text",
                "text": ClaudeCodeMessageProcessor._stringify_content(raw_content),
            }
        ]

    @staticmethod
    def _stringify_payload(payload: dict[str, Any]) -> str:
        """Convert payload to JSON string for Claude SDK ingestion."""

        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return json.dumps(str(payload), ensure_ascii=False)

    @staticmethod
    def _stringify_content(raw_content: Any) -> str:
        """Convert arbitrary content into a Claude-friendly string."""

        if raw_content is None:
            return ""

        if isinstance(raw_content, str):
            return raw_content

        if hasattr(raw_content, "model_dump_json"):
            try:
                return raw_content.model_dump_json()
            except Exception:  # pragma: no cover - fallback for unexpected models
                pass

        if hasattr(raw_content, "model_dump"):
            try:
                return json.dumps(raw_content.model_dump(), ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                return str(raw_content)

        # Always JSON serialize non-string content
        try:
            return json.dumps(raw_content, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(raw_content)

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

        from claude_agent_sdk.types import HookMatcher

        hooks_dict = {}
        for event_type, matchers_list in hooks_config.items():
            event_matchers = []
            for matcher_config in matchers_list:
                hook_matcher = HookMatcher(
                    matcher=matcher_config.get("matcher"), hooks=matcher_config.get("hooks", [])
                )
                event_matchers.append(hook_matcher)

            hooks_dict[event_type] = event_matchers

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
        options_dict = {"system_prompt": system_prompt, "model": "claude-haiku-4-5-20251001"}

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

        # Ensure setting_sources is set to avoid SDK issues with newer CLI versions
        # The SDK always adds --setting-sources flag even when None, but newer CLI doesn't recognize it
        if "setting_sources" not in options_dict:
            options_dict["setting_sources"] = []

        return options_dict
