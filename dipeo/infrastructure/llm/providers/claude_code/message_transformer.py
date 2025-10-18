"""Message transformation utilities for Claude Code SDK.

Handles conversion of DiPeO messages to Claude Code SDK format,
including assistant-to-user transformations and message merging.
"""

import json
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Message

from .content_formatter import build_sdk_content, stringify_content

logger = get_module_logger(__name__)


def prepare_message(messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
    """Convert messages to Claude Code SDK format (system prompt + formatted messages)."""
    system_messages: list[str] = []
    formatted_messages: list[dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role")
            raw_content = msg.get("content", "")
            message_type = msg.get("message_type")

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
            system_messages.append(stringify_content(raw_content).strip() if raw_content else "")
            continue

        message_payload = {
            "role": role,
            "content": build_sdk_content(raw_content),
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
            "content": build_sdk_content(fallback_text),
        }
        formatted_messages.append(
            {
                "type": "user",
                "message": fallback_payload,
            }
        )

    formatted_messages = convert_assistant_to_user_context(formatted_messages)
    formatted_messages = combine_consecutive_user_messages(formatted_messages)

    return system_message, formatted_messages


def convert_assistant_to_user_context(
    formatted_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert assistant messages to user context (SDK limitation workaround)."""
    result = []
    for msg in formatted_messages:
        if msg.get("type") == "assistant":
            msg_data = msg["message"]
            if isinstance(msg_data, str):
                msg_data = json.loads(msg_data)

            content = msg_data.get("content", [])

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


def combine_consecutive_user_messages(
    formatted_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Combine consecutive user messages for proper conversation flow."""
    if not formatted_messages:
        return formatted_messages

    result = []
    current_user_messages = []

    for msg in formatted_messages:
        if msg.get("type") == "user":
            current_user_messages.append(msg)
        else:
            if current_user_messages:
                result.append(merge_user_messages(current_user_messages))
                current_user_messages = []
            result.append(msg)

    if current_user_messages:
        result.append(merge_user_messages(current_user_messages))

    return result


def merge_user_messages(user_messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge multiple user messages into a single message."""
    if len(user_messages) == 1:
        return user_messages[0]

    combined_content = []
    for msg in user_messages:
        msg_data = msg["message"]
        if isinstance(msg_data, str):
            msg_data = json.loads(msg_data)

        content = msg_data.get("content", [])
        if isinstance(content, list):
            combined_content.extend(content)
        else:
            combined_content.append({"type": "text", "text": str(content)})

    return {"type": "user", "message": {"role": "user", "content": combined_content}}


def transform_assistant_memories_to_tool_result(
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

    assistant_indices = []
    for i in range(len(formatted_messages) - 1):
        if formatted_messages[i].get("type") == "assistant":
            assistant_indices.append(i)

    if not assistant_indices:
        return formatted_messages

    result = []
    i = 0
    while i < len(formatted_messages):
        if i not in assistant_indices:
            result.append(formatted_messages[i])
            i += 1
            continue

        memory_messages = []
        start_idx = i
        while i < len(formatted_messages) - 1 and i in assistant_indices:
            memory_messages.append(formatted_messages[i])
            i += 1

        if memory_messages:
            tool_use_id = f"memory_{abs(hash(str(start_idx)))}"

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

            memory_texts = []
            for msg_dict in memory_messages:
                try:
                    msg_data = msg_dict["message"]
                    if isinstance(msg_data, str):
                        msg_data = json.loads(msg_data)

                    content = msg_data.get("content", "")

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
                    logger.warning(f"Failed to parse memory message: {msg_dict}, error: {e}")
                    continue

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
