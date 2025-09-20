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
from .event_turn_processor import EventTurnProcessor

# Use refactored NodeBuilder
from .node_builder_refactored import NodeBuilder


class Converter(BaseConverter):
    """Converts preprocessed session data into DiPeO diagram structures."""

    def __init__(self):
        """Initialize the converter."""
        self.node_builder = NodeBuilder()
        self.connection_builder = ConnectionBuilder()
        # Pass person registry to assembler for better integration
        self.assembler = DiagramAssembler(self.node_builder.person_registry)
        # Initialize event processor with node builder
        self.event_processor = EventTurnProcessor(self.node_builder)

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

            # Process conversation flow
            prev_node_label = start_node_label
            for _i, turn_events in enumerate(conversation_turns):
                try:
                    # Use event processor to handle the turn
                    turn_node_labels = self.event_processor.process_turn(
                        turn_events, preprocessed_data
                    )

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
                    continue

            # Assemble the final diagram
            diagram = self.assembler.assemble_light_diagram(
                nodes=self.node_builder.nodes,
                connections=self.connection_builder.get_connections(),
                persons=self.node_builder.persons,
            )

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
            return report

        except Exception as e:
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
        self.event_processor.reset()

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
            # Start a new turn on non-meta user events that have content
            if event.is_user_event() and not event.is_meta and event.content.has_content():
                # Check if this is the start of a new conversation turn
                # A new turn starts when we encounter a user message after assistant/tool events
                if current_turn and any(
                    e.is_assistant_event() or e.type in [EventType.TOOL_USE, EventType.TOOL_RESULT]
                    for e in current_turn
                ):
                    turns.append(current_turn)
                    current_turn = [event]
                else:
                    # Continue adding to current turn (consecutive user messages or first message)
                    current_turn.append(event)
            else:
                current_turn.append(event)

        # Don't forget the last turn
        if current_turn:
            turns.append(current_turn)

        return turns

    def _extract_initial_prompt(self, preprocessed_data: PreprocessedData) -> str:
        """Extract initial prompt from preprocessed data."""
        # Try to get from metadata first
        if "initial_prompt" in preprocessed_data.conversation_context:
            return preprocessed_data.conversation_context["initial_prompt"]

        # Fall back to first non-meta user event with content
        for event in preprocessed_data.processed_events:
            if event.is_user_event() and not event.is_meta and event.content.has_content():
                return event.content.text or "Claude Code Session"

        return "Claude Code Session"

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
