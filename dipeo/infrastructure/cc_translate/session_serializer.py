"""Session serializer for converting DomainSession to JSONL format.

This module handles the serialization of preprocessed DomainSession objects
back to JSONL format for storage and compatibility with Claude Code format.
"""

import json
from pathlib import Path
from typing import Any, Optional

from dipeo.domain.cc_translate.models.event import DomainEvent, EventType
from dipeo.domain.cc_translate.models.session import DomainSession


class SessionSerializer:
    """Serializes DomainSession objects to various formats including JSONL."""

    def to_jsonl(self, session: DomainSession) -> str:
        """Convert a DomainSession to JSONL format string.

        Args:
            session: The DomainSession to serialize

        Returns:
            JSONL formatted string with one event per line
        """
        lines = []
        for event in session.events:
            event_dict = self._event_to_jsonl_dict(event)
            lines.append(json.dumps(event_dict, ensure_ascii=False))

        # Add final newline if there's content
        if lines:
            return "\n".join(lines) + "\n"
        return ""

    def to_jsonl_file(self, session: DomainSession, file_path: Path) -> int:
        """Write a DomainSession to a JSONL file.

        Args:
            session: The DomainSession to serialize
            file_path: Path to write the JSONL file

        Returns:
            Number of bytes written
        """
        jsonl_content = self.to_jsonl(session)
        file_path.write_text(jsonl_content, encoding="utf-8")
        return len(jsonl_content.encode("utf-8"))

    def _event_to_jsonl_dict(self, event: DomainEvent) -> dict[str, Any]:
        """Convert a DomainEvent to JSONL dictionary format.

        Args:
            event: The DomainEvent to convert

        Returns:
            Dictionary in Claude Code JSONL format
        """
        # Basic event structure
        event_dict = {
            "type": event.type.value if hasattr(event.type, "value") else str(event.type),
            "timestamp": event.timestamp.isoformat()
            if hasattr(event.timestamp, "isoformat")
            else str(event.timestamp),
        }

        # Add UUID if present (not adding empty UUIDs)
        if hasattr(event, "uuid") and event.uuid:
            event_dict["uuid"] = event.uuid

        # Add parent UUID if present
        if hasattr(event, "parent_uuid") and event.parent_uuid:
            event_dict["parentUuid"] = event.parent_uuid

        # Add message content based on event type
        if hasattr(event, "content") and event.content:
            content = event.content

            # Handle user events
            if event.type == EventType.USER:
                # Check if this is a tool result event
                if hasattr(content, "data") and "tool_results" in content.data:
                    # This is a tool result from a user event
                    tool_results = content.data["tool_results"]
                    message_content = []
                    for result in tool_results:
                        # Create tool_result structure
                        message_content.append({"type": "tool_result", "content": result})
                    event_dict["message"] = {
                        "role": "user",
                        "content": message_content if message_content else tool_results,
                    }
                elif hasattr(content, "text") and content.text:
                    event_dict["message"] = {"role": "user", "content": content.text}
                elif hasattr(content, "data") and content.data:
                    # Handle structured user content
                    event_dict["message"] = {"role": "user", "content": content.data}

            # Handle assistant events
            elif event.type == EventType.ASSISTANT:
                message_content = []

                # Add text content
                if hasattr(content, "text") and content.text:
                    message_content.append({"type": "text", "text": content.text})

                # Add tool use if present
                if hasattr(event, "tool_info") and event.tool_info:
                    tool_info = event.tool_info
                    tool_use_block = {
                        "type": "tool_use",
                        "name": tool_info.name,
                    }
                    if tool_info.input_params:
                        tool_use_block["input"] = tool_info.input_params
                    message_content.append(tool_use_block)

                    # Add tool results if present
                    if tool_info.results:
                        for result in tool_info.results:
                            message_content.append({"type": "tool_result", "content": result})

                # Create assistant message
                if message_content:
                    event_dict["message"] = {"role": "assistant", "content": message_content}

            # Handle summary events
            elif event.type == EventType.SUMMARY:
                if hasattr(content, "text") and content.text:
                    event_dict["summary"] = content.text

            # Handle system events
            elif event.type == EventType.SYSTEM:
                if hasattr(content, "text") and content.text:
                    event_dict["system"] = content.text
                elif hasattr(content, "data") and content.data:
                    event_dict["system"] = content.data

            # Add tool results from content data if present
            if hasattr(content, "data") and content.data:
                if "tool_results" in content.data:
                    event_dict["toolUseResult"] = content.data["tool_results"]
                if "tool_input" in content.data and "tool_name" not in event_dict:
                    # Add tool input if not already added via tool_info
                    event_dict["toolInput"] = content.data["tool_input"]

        # Add meta flag if present and true
        if hasattr(event, "is_meta") and event.is_meta:
            event_dict["isMeta"] = True

        # Add user type if present
        if hasattr(event, "user_type") and event.user_type:
            event_dict["userType"] = event.user_type

        # Add role if not already in message
        if hasattr(event, "role") and event.role and "message" not in event_dict:
            event_dict["role"] = (
                event.role.value if hasattr(event.role, "value") else str(event.role)
            )

        # Add tags if present and non-empty
        if hasattr(event, "tags") and event.tags:
            event_dict["tags"] = event.tags

        # Add context if present and non-empty
        if hasattr(event, "context") and event.context:
            event_dict["context"] = event.context

        return event_dict

    def calculate_size_reduction(
        self, original_path: Path, preprocessed_session: DomainSession
    ) -> tuple[int, int, float]:
        """Calculate size reduction from preprocessing.

        Args:
            original_path: Path to original JSONL file
            preprocessed_session: The preprocessed DomainSession

        Returns:
            Tuple of (original_size, preprocessed_size, reduction_percentage)
        """
        original_size = original_path.stat().st_size
        preprocessed_jsonl = self.to_jsonl(preprocessed_session)
        preprocessed_size = len(preprocessed_jsonl.encode("utf-8"))

        reduction_pct = 0.0
        if original_size > 0:
            reduction_pct = ((original_size - preprocessed_size) / original_size) * 100

        return original_size, preprocessed_size, reduction_pct
