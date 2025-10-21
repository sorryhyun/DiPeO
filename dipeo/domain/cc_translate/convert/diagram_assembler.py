"""Diagram assembler for Claude Code translation.

This module handles the final assembly of nodes, connections, and metadata
into the light format diagram structure.
"""

from typing import Any, Optional

from .person_registry import PersonRegistry


class DiagramAssembler:
    """Assembles final light format diagram from components."""

    def __init__(self, person_registry: PersonRegistry | None = None):
        self.person_registry = person_registry

    def assemble_light_diagram(
        self,
        nodes: list[dict[str, Any]],
        connections: list[dict[str, Any]],
        persons: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Build the light format diagram
        diagram = {"version": "light"}

        # Add nodes
        if nodes:
            diagram["nodes"] = nodes

        # Add connections
        if connections:
            diagram["connections"] = connections

        # Add persons section if we have AI agents
        # Use provided persons or get from registry
        if persons:
            diagram["persons"] = persons
        elif self.person_registry:
            registry_persons = self.person_registry.get_all_persons()
            if registry_persons:
                diagram["persons"] = registry_persons

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
        if "metadata" not in diagram:
            diagram["metadata"] = {}

        # Add preprocessing metadata if pruning was applied
        if preprocessing_report:
            # Handle both dict and object formats
            if isinstance(preprocessing_report, dict):
                # Dictionary format from _extract_preprocessing_report
                if preprocessing_report.get("changes", 0) > 0:
                    diagram["metadata"]["preprocessing"] = {
                        "session_event_pruning": {
                            "applied": True,
                            "changes_count": preprocessing_report.get("changes", 0),
                            "stats": preprocessing_report.get("stats", {}),
                            "stage": preprocessing_report.get("stage", "unknown"),
                            "warnings": preprocessing_report.get("warnings", []),
                            "errors": preprocessing_report.get("errors", []),
                        }
                    }
            elif hasattr(preprocessing_report, "has_changes"):
                # Object format (for future compatibility)
                if preprocessing_report.has_changes():
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
