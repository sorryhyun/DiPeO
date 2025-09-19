"""Main diagram converter for Claude Code translation.

This module handles the conversion phase: transforming preprocessed session
data into DiPeO diagram structures with nodes, connections, and persons.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from ..models.event import DomainEvent, EventType
from ..models.preprocessed import PreprocessedData
from .base import BaseConverter, ConversionContext, ConversionReport, ConversionStatus
from .connection_builder import ConnectionBuilder
from .diagram_assembler import DiagramAssembler
from .node_builders import NodeBuilder


class Converter(BaseConverter):
    """Converts preprocessed session data into DiPeO diagram structures."""

    def __init__(self):
        """Initialize the converter."""
        self.node_builder = NodeBuilder()
        self.connection_builder = ConnectionBuilder()
        self.assembler = DiagramAssembler()
        self.node_map: dict[str, str] = {}  # Maps event UUID to node label

    def convert(
        self,
        preprocessed_data: PreprocessedData,
        context: Optional[ConversionContext] = None,
    ) -> ConversionReport:
        """
        Convert preprocessed data into a diagram.

        Args:
            preprocessed_data: The preprocessed session data to convert
            context: Optional conversion context for tracking

        Returns:
            A ConversionReport containing the result and metrics
        """
        # Create context if not provided
        if not context:
            context = self.create_context(preprocessed_data.session.session_id)

        context.start()

        try:
            # Validate input
            if not self.validate_input(preprocessed_data):
                context.add_error("Invalid preprocessed data")
                context.complete(success=False)
                return self._create_report(context, None)

            # Debug: Print info about preprocessed data
            print(f"[DEBUG] Processing session {preprocessed_data.session.session_id}")
            print(f"[DEBUG] Number of processed events: {len(preprocessed_data.processed_events)}")
            print(
                f"[DEBUG] Event types: {[e.type.value if hasattr(e.type, 'value') else str(e.type) for e in preprocessed_data.processed_events[:5]]}"
            )

            # Reset state for new conversion
            self._reset_state()

            # Extract metadata from session
            session_id = preprocessed_data.session.session_id
            initial_prompt = self._extract_initial_prompt(preprocessed_data)

            # Create start node
            start_node_label = self._create_start_node(session_id, initial_prompt)
            if not start_node_label:
                context.add_error("Failed to create start node")
                context.complete(success=False)
                return self._create_report(context, None)

            # Group events into conversation turns
            conversation_turns = self._group_events_into_turns(preprocessed_data.processed_events)
            print(f"[DEBUG] Number of conversation turns: {len(conversation_turns)}")

            # Process conversation flow
            prev_node_label = start_node_label
            for i, turn_events in enumerate(conversation_turns):
                print(
                    f"[DEBUG] Processing turn {i+1}/{len(conversation_turns)}, {len(turn_events)} events"
                )
                try:
                    turn_node_labels = self._process_event_turn(turn_events, preprocessed_data)
                    print(f"[DEBUG] Created {len(turn_node_labels)} nodes from turn")

                    # Connect to previous node
                    if turn_node_labels:
                        self.connection_builder.connect_to_previous(
                            prev_node_label, turn_node_labels
                        )
                        self.connection_builder.connect_sequential_nodes(turn_node_labels)
                        prev_node_label = turn_node_labels[-1]

                    context.metrics.nodes_processed += len(turn_events)
                    context.metrics.nodes_created += len(turn_node_labels)

                except Exception as e:
                    context.add_warning(f"Error processing turn: {e!s}")
                    print(f"[DEBUG] Error processing turn: {e!s}")
                    continue

            # Assemble the final diagram
            print(f"[DEBUG] Total nodes to assemble: {len(self.node_builder.nodes)}")
            print(f"[DEBUG] Total connections: {len(self.connection_builder.get_connections())}")
            print(f"[DEBUG] Total persons: {len(self.node_builder.persons)}")
            diagram = self.assembler.assemble_light_diagram(
                nodes=self.node_builder.nodes,
                connections=self.connection_builder.get_connections(),
                persons=self.node_builder.persons,
            )
            print(f"[DEBUG] Assembled diagram has {len(diagram.get('nodes', []))} nodes")

            # Add processing metadata
            diagram = self.assembler.add_processing_metadata(
                diagram=diagram,
                preprocessing_report=self._extract_preprocessing_report(preprocessed_data),
                conversion_stats=self._get_conversion_stats(),
            )

            # Update metrics
            context.metrics.connections_created = len(self.connection_builder.get_connections())
            context.complete(success=True)

            report = self._create_report(context, diagram)
            print(f"[DEBUG] Report has diagram: {report.diagram is not None}")
            if report.diagram:
                print(f"[DEBUG] Report diagram has {len(report.diagram.get('nodes', []))} nodes")
            return report

        except Exception as e:
            print(f"[DEBUG ERROR] Conversion exception: {e!s}")
            import traceback

            traceback.print_exc()
            context.add_error(f"Conversion failed: {e!s}")
            context.complete(success=False)
            return self._create_report(context, None)

    def validate_input(self, preprocessed_data: PreprocessedData) -> bool:
        """
        Validate that the input data can be converted.

        Args:
            preprocessed_data: The preprocessed data to validate

        Returns:
            True if the data is valid for conversion, False otherwise
        """
        if not preprocessed_data:
            return False

        if not preprocessed_data.session:
            return False

        # Validate preprocessed data integrity
        validation_errors = preprocessed_data.validate()
        if validation_errors:
            return False

        return True

    def _reset_state(self) -> None:
        """Reset converter state for new conversion."""
        self.node_builder.reset()
        self.connection_builder.reset()
        self.node_map = {}

    def _create_start_node(self, session_id: str, initial_prompt: str) -> str:
        """Create the start node for the diagram."""
        node = self.node_builder.create_start_node(session_id, initial_prompt)
        return node["label"]

    def _group_events_into_turns(self, events: list[DomainEvent]) -> list[list[DomainEvent]]:
        """
        Group events into conversation turns.

        A turn typically consists of:
        - User event(s)
        - Assistant event(s)
        - Tool use event(s) if any

        Args:
            events: List of domain events

        Returns:
            List of event groups representing conversation turns
        """
        turns = []
        current_turn = []

        for event in events:
            # Start a new turn on user events (unless it's a tool result response)
            if event.is_user_event() and not event.parent_uuid:
                if current_turn:
                    turns.append(current_turn)
                current_turn = [event]
            else:
                current_turn.append(event)

        # Don't forget the last turn
        if current_turn:
            turns.append(current_turn)

        return turns

    def _process_event_turn(
        self, turn_events: list[DomainEvent], preprocessed_data: PreprocessedData
    ) -> list[str]:
        """Process a turn of events and create corresponding nodes."""
        node_labels = []

        # Extract system messages from preprocessed data
        system_messages = self._extract_system_messages(preprocessed_data)

        for event in turn_events:
            if event.is_user_event():
                # Skip user events that are just showing tool results
                if not event.parent_uuid:
                    user_node_label = self._create_user_node_from_event(event)
                    if user_node_label:
                        node_labels.append(user_node_label)

            elif event.is_assistant_event():
                # Check if this assistant event has tool usage
                if event.has_tool_use():
                    tool_node_labels = self._create_tool_nodes_from_event(event)
                    node_labels.extend(tool_node_labels)
                else:
                    assistant_node_label = self._create_assistant_node_from_event(
                        event, system_messages
                    )
                    if assistant_node_label:
                        node_labels.append(assistant_node_label)

            elif event.type == EventType.TOOL_USE or event.type == EventType.TOOL_RESULT:
                tool_node_labels = self._create_tool_nodes_from_event(event)
                node_labels.extend(tool_node_labels)

        return node_labels

    def _create_user_node_from_event(self, event: DomainEvent) -> Optional[str]:
        """Create a node for user input from domain event."""
        content = event.content.text or ""

        # Skip empty content
        if not content.strip():
            return None

        node = self.node_builder.create_user_node(content)
        if node:
            self.node_map[event.uuid] = node["label"]
            return node["label"]
        return None

    def _create_assistant_node_from_event(
        self, event: DomainEvent, system_messages: list[str]
    ) -> Optional[str]:
        """Create a node for AI assistant response from domain event."""
        content = event.content.text or ""

        if not content.strip():
            return None

        node = self.node_builder.create_assistant_node(content, system_messages)
        if node:
            self.node_map[event.uuid] = node["label"]
            return node["label"]
        return None

    def _create_tool_nodes_from_event(self, event: DomainEvent) -> list[str]:
        """Create nodes for tool usage from domain event."""
        node_labels = []

        if not event.tool_info:
            return node_labels

        tool_name = event.tool_info.name
        tool_input = event.tool_info.input_params
        tool_results = event.tool_info.results if event.tool_info.results else None

        # Create appropriate node for the tool
        node = self.node_builder.create_tool_node(tool_name, tool_input, tool_results)

        if node:
            node_labels.append(node["label"])
            self.node_map[event.uuid] = node["label"]

        return node_labels

    def _extract_initial_prompt(self, preprocessed_data: PreprocessedData) -> str:
        """Extract initial prompt from preprocessed data."""
        # Try to get from metadata first
        if "initial_prompt" in preprocessed_data.conversation_context:
            return preprocessed_data.conversation_context["initial_prompt"]

        # Fall back to first user event
        for event in preprocessed_data.processed_events:
            if event.is_user_event():
                return event.content.text or "Claude Code Session"

        return "Claude Code Session"

    def _extract_system_messages(self, preprocessed_data: PreprocessedData) -> list[str]:
        """Extract system messages from preprocessed data."""
        system_messages = []

        # Extract from events
        for event in preprocessed_data.processed_events:
            if event.is_system_event() and event.content.text:
                system_messages.append(event.content.text)

        # Also check conversation context
        if "system_messages" in preprocessed_data.conversation_context:
            additional_messages = preprocessed_data.conversation_context["system_messages"]
            if isinstance(additional_messages, list):
                system_messages.extend(additional_messages)

        return system_messages[:5]  # Limit to first 5 messages

    def _extract_preprocessing_report(self, preprocessed_data: PreprocessedData) -> dict[str, Any]:
        """Extract preprocessing report from preprocessed data."""
        return {
            "changes": len(preprocessed_data.changes),
            "stats": preprocessed_data.stats.to_dict(),
            "stage": preprocessed_data.stage.value,
            "warnings": preprocessed_data.warnings,
            "errors": preprocessed_data.errors,
        }

    def _create_report(
        self, context: ConversionContext, diagram: Optional[dict[str, Any]]
    ) -> ConversionReport:
        """Create a conversion report."""
        return ConversionReport(
            session_id=context.session_id,
            conversion_id=context.conversion_id,
            status=context.status,
            diagram=diagram,
            metrics=context.metrics,
            metadata=context.metadata,
        )

    def _get_conversion_stats(self) -> dict[str, Any]:
        """Get conversion statistics."""
        return {
            "total_nodes": len(self.node_builder.nodes),
            "total_connections": len(self.connection_builder.get_connections()),
            "total_persons": len(self.node_builder.persons),
            "node_types": self._count_node_types(),
        }

    def _count_node_types(self) -> dict[str, int]:
        """Count nodes by type."""
        type_counts = {}
        for node in self.node_builder.nodes:
            node_type = node.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
