"""Message processing utilities for Claude Code provider.

This module provides a facade over specialized submodules:
- content_formatter: Content conversion utilities
- prompt_builder: System prompt generation
- message_transformer: Message transformation logic
- options_builder: Tool and hook configuration

For backwards compatibility, this module re-exports all public functions
through the ClaudeCodeMessageProcessor class.
"""

from .content_formatter import build_sdk_content, stringify_content, stringify_payload
from .message_transformer import (
    combine_consecutive_user_messages,
    convert_assistant_to_user_context,
    merge_user_messages,
    prepare_message,
    transform_assistant_memories_to_tool_result,
)
from .options_builder import build_claude_options, create_tool_options, format_hooks_config
from .prompt_builder import build_system_prompt, get_system_prompt


class ClaudeCodeMessageProcessor:
    """Facade for message processing utilities (backwards compatibility)."""

    get_system_prompt = staticmethod(get_system_prompt)
    prepare_message = staticmethod(prepare_message)
    _convert_assistant_to_user_context = staticmethod(convert_assistant_to_user_context)
    _combine_consecutive_user_messages = staticmethod(combine_consecutive_user_messages)
    _merge_user_messages = staticmethod(merge_user_messages)
    _transform_assistant_memories_to_tool_result = staticmethod(
        transform_assistant_memories_to_tool_result
    )
    _build_sdk_content = staticmethod(build_sdk_content)
    _stringify_payload = staticmethod(stringify_payload)
    _stringify_content = staticmethod(stringify_content)
    create_tool_options = staticmethod(create_tool_options)
    format_hooks_config = staticmethod(format_hooks_config)
    build_system_prompt = staticmethod(build_system_prompt)
    build_claude_options = staticmethod(build_claude_options)


__all__ = [
    "ClaudeCodeMessageProcessor",
    "build_claude_options",
    "build_sdk_content",
    "build_system_prompt",
    "combine_consecutive_user_messages",
    "convert_assistant_to_user_context",
    "create_tool_options",
    "format_hooks_config",
    "get_system_prompt",
    "merge_user_messages",
    "prepare_message",
    "stringify_content",
    "stringify_payload",
    "transform_assistant_memories_to_tool_result",
]
