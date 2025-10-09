"""Infrastructure adapters for converting Claude Code sessions to domain models.

This module provides adapters to convert between infrastructure layer
types (like ClaudeCodeSession) and domain layer ports/models.
"""

from datetime import datetime
from typing import Optional

from dipeo.domain.cc_translate.models.event import (
    DomainEvent,
    EventContent,
    EventRole,
    EventType,
    ToolInfo,
)
from dipeo.domain.cc_translate.models.session import DomainSession, SessionMetadata

from .session_parser import ClaudeCodeSession


class SessionAdapter:
    """Adapter to convert ClaudeCodeSession to DomainSession.

    This adapter converts infrastructure types to domain models
    for use with domain layer components.
    """

    def __init__(self, session: ClaudeCodeSession):
        """Initialize the adapter with an infrastructure session.

        Args:
            session: The infrastructure ClaudeCodeSession to adapt
        """
        self._session = session
        self._domain_session = None

    def to_domain_session(self) -> DomainSession:
        """Convert infrastructure session to domain model.

        Returns:
            DomainSession with properly converted events and metadata
        """
        if self._domain_session is None:
            # Convert metadata
            metadata = SessionMetadata(
                session_id=self._session.session_id,
                start_time=self._session.metadata.start_time
                if hasattr(self._session.metadata, "start_time")
                else None,
                end_time=self._session.metadata.end_time
                if hasattr(self._session.metadata, "end_time")
                else None,
                event_count=len(self._session.events),
                tool_usage_count=self._session.extract_tool_usage()
                if hasattr(self._session, "extract_tool_usage")
                else {},
                file_operations=self._session.metadata.file_operations
                if hasattr(self._session.metadata, "file_operations")
                else {},
            )

            # Convert events
            domain_events = []
            for event in self._session.events:
                domain_event = self._convert_event(event)
                if domain_event:
                    domain_events.append(domain_event)

            # Create domain session
            self._domain_session = DomainSession(
                session_id=self._session.session_id,
                events=domain_events,
                metadata=metadata,
                conversation_turns=getattr(self._session, "conversation_turns", []),
            )

        return self._domain_session

    def _convert_event(self, infra_event) -> DomainEvent | None:
        """Convert infrastructure event to domain event.

        Args:
            infra_event: Infrastructure layer event

        Returns:
            DomainEvent or None if conversion fails
        """
        # Determine event type
        event_type = self._get_event_type(infra_event)

        # Determine role
        role = None
        if event_type == EventType.USER:
            role = EventRole.USER
        elif event_type == EventType.ASSISTANT:
            role = EventRole.ASSISTANT
        elif event_type == EventType.SYSTEM:
            role = EventRole.SYSTEM

        # Create content
        content = self._create_event_content(infra_event)

        # Create tool info if applicable
        tool_info = None
        if hasattr(infra_event, "tool_name") and infra_event.tool_name:
            tool_info = ToolInfo(
                name=infra_event.tool_name,
                input_params=infra_event.tool_input if hasattr(infra_event, "tool_input") else {},
                results=infra_event.tool_results if hasattr(infra_event, "tool_results") else [],
                status="success" if hasattr(infra_event, "tool_results") else "pending",
            )
        elif event_type == EventType.TOOL_RESULT and hasattr(infra_event, "tool_use_result"):
            # For TOOL_RESULT events from USER events with toolUseResult
            # Try to get the tool name from the parent event's tool_name if available
            tool_name = "tool_result"  # Default generic name

            # If we have a parent_uuid, we might be able to get the actual tool name
            # The session parser should have associated the result with its parent tool event
            if hasattr(infra_event, "parent_uuid") and infra_event.parent_uuid:
                # Note: We'd need access to all events to look up the parent
                # For now, we'll just mark it as a generic tool_result
                pass

            tool_info = ToolInfo(
                name=tool_name,
                input_params={},
                results=[infra_event.tool_use_result] if infra_event.tool_use_result else [],
                status="success",
            )

        # Create domain event
        return DomainEvent(
            uuid=infra_event.uuid if hasattr(infra_event, "uuid") else str(id(infra_event)),
            type=event_type,
            timestamp=infra_event.timestamp
            if hasattr(infra_event, "timestamp")
            else datetime.now(),
            content=content,
            parent_uuid=infra_event.parent_uuid if hasattr(infra_event, "parent_uuid") else None,
            role=role,
            tool_info=tool_info,
            is_meta=infra_event.is_meta if hasattr(infra_event, "is_meta") else False,
        )

    def _get_event_type(self, event) -> EventType:
        """Determine the event type from infrastructure event."""
        if hasattr(event, "type"):
            event_type_str = event.type.lower()
            if event_type_str == "user":
                # Check if this is actually a tool result masquerading as a user event
                if hasattr(event, "tool_use_result") and event.tool_use_result:
                    return EventType.TOOL_RESULT
                return EventType.USER
            elif event_type_str == "assistant":
                return EventType.ASSISTANT
            elif event_type_str == "summary":
                return EventType.SUMMARY
            elif event_type_str == "system":
                return EventType.SYSTEM
            elif "tool" in event_type_str:
                return EventType.TOOL_USE

        # Default to assistant if unknown
        return EventType.ASSISTANT

    def _create_event_content(self, event) -> EventContent:
        """Create event content from infrastructure event."""
        text = None
        data = {}

        # Handle tool_use_result if present (from USER events with tool results)
        if hasattr(event, "tool_use_result") and event.tool_use_result:
            # Store the tool result payload
            data["tool_result_payload"] = event.tool_use_result
            # Extract text content if it's a list (file content)
            if isinstance(event.tool_use_result, list) and event.tool_use_result:
                # Join lines if it's file content
                text = "\n".join(str(line) for line in event.tool_use_result)
            else:
                text = str(event.tool_use_result)
            return EventContent(text=text, data=data)

        # Extract text content
        if hasattr(event, "message") and event.message:
            # Extract content from message structure
            if isinstance(event.message, dict):
                if "content" in event.message:
                    content = event.message["content"]
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        # Extract text from content list (for assistant messages)
                        text_parts = []
                        tool_results = []
                        for item in content:
                            if isinstance(item, dict):
                                if "text" in item:
                                    text_parts.append(item["text"])
                                elif item.get("type") == "tool_result":
                                    # Store tool result content
                                    if "content" in item:
                                        tool_results.append(item["content"])
                            elif isinstance(item, str):
                                text_parts.append(item)

                        if text_parts:
                            text = "\n".join(text_parts)
                        elif tool_results:
                            # If no text but has tool results, use those as text
                            text = "\n".join(str(r) for r in tool_results)

                        # Store tool results in data
                        if tool_results:
                            data["tool_results"] = tool_results
                    else:
                        # Store entire content if not string or list
                        text = str(content)
                else:
                    # No content field, store entire message
                    text = str(event.message)
            else:
                text = str(event.message)
        elif hasattr(event, "content"):
            if isinstance(event.content, str):
                text = event.content
            elif isinstance(event.content, list):
                # Extract text from content list
                text_parts = []
                for item in event.content:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    elif isinstance(item, str):
                        text_parts.append(item)
                if text_parts:
                    text = "\n".join(text_parts)

        # Add tool-related data if present
        if hasattr(event, "tool_input") and event.tool_input:
            data["tool_input"] = event.tool_input
        if hasattr(event, "tool_results") and event.tool_results:
            data["tool_results"] = event.tool_results

        return EventContent(text=text, data=data)

    # Legacy SessionPort compatibility methods (for backward compatibility)
    @property
    def id(self) -> str:
        """Get the session identifier (for SessionPort compatibility)."""
        return self._session.session_id

    @property
    def session_id(self) -> str:
        """Get the session identifier."""
        return self._session.session_id

    @property
    def events(self) -> list:
        """Get all events in the session (converts to domain events)."""
        return self.to_domain_session().events

    @property
    def metadata(self) -> SessionMetadata:
        """Get session metadata (as domain model)."""
        return self.to_domain_session().metadata

    @property
    def start_time(self) -> datetime | None:
        """Get session start time."""
        return self.to_domain_session().metadata.start_time

    @property
    def end_time(self) -> datetime | None:
        """Get session end time."""
        return self.to_domain_session().metadata.end_time

    def get_event_count(self) -> int:
        """Get total number of events."""
        return len(self.to_domain_session().events)

    def get_tool_usage_stats(self) -> dict[str, int]:
        """Get tool usage statistics."""
        return self.to_domain_session().metadata.tool_usage_count

    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        return self.to_domain_session().to_dict()
