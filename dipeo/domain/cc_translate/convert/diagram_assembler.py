"""Diagram assembler for Claude Code translation.

This module handles the final assembly of nodes, connections, and metadata
into the light format diagram structure.
"""

from typing import Any


class DiagramAssembler:
    """Assembles final light format diagram from components."""

    def __init__(self):
        """Initialize the diagram assembler."""
        pass

    def assemble_light_diagram(
        self,
        nodes: list[dict[str, Any]],
        connections: list[dict[str, Any]],
        persons: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Assemble components into light format diagram.

        Args:
            nodes: List of node dictionaries
            connections: List of connection dictionaries
            persons: Dictionary of person configurations
            metadata: Optional metadata to include

        Returns:
            Complete light format diagram dictionary
        """
        # Build the light format diagram
        diagram = {"version": "light"}

        # Add nodes
        if nodes:
            diagram["nodes"] = nodes

        # Add connections
        if connections:
            diagram["connections"] = connections

        # Add persons section if we have AI agents
        if persons:
            diagram["persons"] = persons

        # Add metadata if provided
        if metadata:
            diagram["metadata"] = metadata

        return diagram

    def add_processing_metadata(
        self,
        diagram: dict[str, Any],
        preprocessing_report: Any = None,
        conversion_stats: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add processing metadata to the diagram.

        Args:
            diagram: The diagram to add metadata to
            preprocessing_report: Optional preprocessing report
            conversion_stats: Optional conversion statistics

        Returns:
            Updated diagram with metadata
        """
        if "metadata" not in diagram:
            diagram["metadata"] = {}

        # Add preprocessing metadata if pruning was applied
        if preprocessing_report and preprocessing_report.has_changes():
            diagram["metadata"]["preprocessing"] = {
                "session_event_pruning": {
                    "applied": True,
                    "events_pruned": preprocessing_report.nodes_removed,
                    "pruning_time_ms": preprocessing_report.processing_time_ms,
                    "changes": [
                        {
                            "type": change.change_type.value,
                            "description": change.description,
                            "target": change.target,
                        }
                        for change in preprocessing_report.changes
                    ],
                }
            }

        # Add conversion statistics
        if conversion_stats:
            diagram["metadata"]["conversion"] = conversion_stats

        return diagram
