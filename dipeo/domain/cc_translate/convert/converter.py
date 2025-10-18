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
from .node_builder_refactored import NodeBuilder


class Converter(BaseConverter):
    """Converts preprocessed session data into DiPeO diagram structures."""

    def __init__(self):
        self.node_builder = NodeBuilder()
        self.connection_builder = ConnectionBuilder()
        self.assembler = DiagramAssembler(self.node_builder.person_registry)
        self.event_processor = EventTurnProcessor(self.node_builder)

    def convert(
        self,
        preprocessed_data: PreprocessedData,
        context: ConversionContext | None = None,
    ) -> ConversionReport:
        """
        Convert preprocessed data into a diagram.

        Args:
            preprocessed_data: The preprocessed session data to convert
            context: Optional conversion context for tracking

        Returns:
            A ConversionReport containing the result and metrics
        """
        if not context:
            context = self.create_context(preprocessed_data.session.session_id)

        context.start()

        try:
            if not self.validate_input(preprocessed_data):
                context.add_error("Invalid preprocessed data")
                context.complete(success=False)
                return self._create_report(context, None)

            self._reset_state()

            session_id = preprocessed_data.session.session_id
            initial_prompt = self._extract_initial_prompt(preprocessed_data)

            start_node_label = self._create_start_node(session_id, initial_prompt)
            if not start_node_label:
                context.add_error("Failed to create start node")
                context.complete(success=False)
                return self._create_report(context, None)

            conversation_turns = self._group_events_into_turns(preprocessed_data.processed_events)

            prev_node_label = start_node_label
            for _i, turn_events in enumerate(conversation_turns):
                try:
                    turn_node_labels = self.event_processor.process_turn(
                        turn_events, preprocessed_data
                    )

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

            diagram = self.assembler.assemble_light_diagram(
                nodes=self.node_builder.nodes,
                connections=self.connection_builder.get_connections(),
                persons=self.node_builder.persons,
            )

            diagram = self.assembler.add_processing_metadata(
                diagram=diagram,
                preprocessing_report=self._extract_preprocessing_report(preprocessed_data),
                conversion_stats=self._get_conversion_stats(),
            )

            context.metrics.connections_created = len(self.connection_builder.get_connections())
            context.complete(success=True)

            report = self._create_report(context, diagram)
            return report

        except Exception as e:
            context.add_error(f"Conversion failed: {e!s}")
            context.complete(success=False)
            return self._create_report(context, None)

    def validate_input(self, preprocessed_data: PreprocessedData) -> bool:
        if not preprocessed_data:
            return False

        if not preprocessed_data.session:
            return False

        validation_errors = preprocessed_data.validate()
        if validation_errors:
            return False

        return True

    def _reset_state(self) -> None:
        self.node_builder.reset()
        self.connection_builder.reset()
        self.event_processor.reset()

    def _create_start_node(self, session_id: str, initial_prompt: str) -> str:
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
            if event.is_user_event() and not event.is_meta and event.content.has_content():
                # New turn starts when encountering a user message after assistant/tool events
                if current_turn and any(
                    e.is_assistant_event() or e.type in [EventType.TOOL_USE, EventType.TOOL_RESULT]
                    for e in current_turn
                ):
                    turns.append(current_turn)
                    current_turn = [event]
                else:
                    current_turn.append(event)
            else:
                current_turn.append(event)

        if current_turn:
            turns.append(current_turn)

        return turns

    def _extract_initial_prompt(self, preprocessed_data: PreprocessedData) -> str:
        if "initial_prompt" in preprocessed_data.conversation_context:
            return preprocessed_data.conversation_context["initial_prompt"]

        for event in preprocessed_data.processed_events:
            if event.is_user_event() and not event.is_meta and event.content.has_content():
                return event.content.text or "Claude Code Session"

        return "Claude Code Session"

    def _extract_preprocessing_report(self, preprocessed_data: PreprocessedData) -> dict[str, Any]:
        return {
            "changes": len(preprocessed_data.changes),
            "stats": preprocessed_data.stats.to_dict(),
            "stage": preprocessed_data.stage.value,
            "warnings": preprocessed_data.warnings,
            "errors": preprocessed_data.errors,
        }

    def _create_report(
        self, context: ConversionContext, diagram: dict[str, Any] | None
    ) -> ConversionReport:
        return ConversionReport(
            session_id=context.session_id,
            conversion_id=context.conversion_id,
            status=context.status,
            diagram=diagram,
            metrics=context.metrics,
            metadata=context.metadata,
        )

    def _get_conversion_stats(self) -> dict[str, Any]:
        return {
            "total_nodes": len(self.node_builder.nodes),
            "total_connections": len(self.connection_builder.get_connections()),
            "total_persons": len(self.node_builder.persons),
            "node_types": self._count_node_types(),
        }

    def _count_node_types(self) -> dict[str, int]:
        type_counts = {}
        for node in self.node_builder.nodes:
            node_type = node.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
