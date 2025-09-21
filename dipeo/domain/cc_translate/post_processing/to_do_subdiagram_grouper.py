"""Processor to group diagram nodes by to-do updates into sub-diagrams."""

import os
import time
from pathlib import Path
from typing import Any, Optional

import yaml

from .base import BaseDiagramProcessor, DiagramChange, DiagramChangeType, DiagramProcessingReport


class To_Do_Subdiagram_Grouper(BaseDiagramProcessor):
    """
    Groups diagram nodes based on to-do updates into hierarchical sub-diagrams.

    This processor analyzes a diagram for to-do update nodes and creates:
    1. Individual sub-diagram files for each to-do group
    2. A main grouped diagram with sequential sub_diagram nodes

    to-do update nodes are identified as db nodes with:
    - operation: write
    - sub_type: memory
    - query: UPDATE TO_DO LIST
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize with configuration."""
        super().__init__(config)
        self.output_subdirectory = self.config.get("output_subdirectory", "grouped")
        self.preserve_connections = self.config.get("preserve_connections", True)
        self.naming_convention = self.config.get("naming_convention", "to-do")

        # New configuration options for TODO extraction
        self.extract_todos_to_main = self.config.get("extract_todos_to_main", True)
        self.min_nodes_for_subdiagram = self.config.get("min_nodes_for_subdiagram", 3)
        self.skip_trivial_subdiagrams = self.config.get("skip_trivial_subdiagrams", True)

    @property
    def name(self) -> str:
        """Return processor name."""
        return "To_Do_Subdiagram_Grouper"

    def process_diagram(
        self, diagram: dict[str, Any]
    ) -> tuple[dict[str, Any], DiagramProcessingReport]:
        """
        Process diagram to group nodes by to-do updates.

        Args:
            diagram: The diagram to process

        Returns:
            Tuple of (grouped diagram, report)
        """
        start_time = time.time()
        report = DiagramProcessingReport(processor_name=self.name)

        # Check applicability
        if not self.is_applicable(diagram):
            return diagram, report

        try:
            # Clone diagram for processing
            processed = self._clone_diagram(diagram)

            # Find to-do update nodes
            to_do_nodes, to_do_nodes_map = self._find_to_do_update_nodes(processed["nodes"])

            if not to_do_nodes:
                # No to-do updates found, return original
                report.processing_time_ms = (time.time() - start_time) * 1000
                return diagram, report

            # Group nodes by to-do updates (now with TODO extraction if enabled)
            node_groups, extracted_todos = self._group_nodes_by_to_dos(
                processed, to_do_nodes, to_do_nodes_map
            )

            # Check if we should create sub-diagrams or just a linear TODO flow
            if not node_groups or (self.extract_todos_to_main and len(node_groups) == 0):
                # No meaningful work groups, create linear TODO flow
                grouped_diagram = self._create_linear_todo_flow(processed, extracted_todos, report)
            elif len(node_groups) <= 1 and not self.extract_todos_to_main:
                # Not enough groups to warrant sub-diagram creation (original behavior)
                report.processing_time_ms = (time.time() - start_time) * 1000
                return diagram, report
            else:
                # Create sub-diagrams and main grouped diagram with extracted TODOs
                grouped_diagram = self._create_grouped_diagram(
                    processed, node_groups, extracted_todos, report
                )

            report.add_change(
                DiagramChange(
                    change_type=DiagramChangeType.METADATA_UPDATED,
                    description=f"Created {len(node_groups)} sub-diagrams based on TODO updates",
                    target="diagram_structure",
                    details={
                        "original_nodes": len(processed["nodes"]),
                        "grouped_nodes": len(grouped_diagram["nodes"]),
                        "sub_diagrams_created": len(node_groups),
                    },
                )
            )

        except Exception as e:
            report.error = f"Error during TODO grouping: {e!s}"
            return diagram, report

        finally:
            report.processing_time_ms = (time.time() - start_time) * 1000

        return grouped_diagram, report

    def _find_to_do_update_nodes(
        self, nodes: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """
        Find all to-do update nodes in the diagram and track their positions.

        Args:
            nodes: List of nodes to analyze

        Returns:
            Tuple of (todo_nodes_list, todo_nodes_map) where map is label -> node
        """
        todo_nodes = []
        todo_nodes_map = {}

        for node in nodes:
            if (
                node.get("type") == "db"
                and node.get("props", {}).get("operation") == "write"
                and node.get("props", {}).get("sub_type") == "memory"
                and node.get("props", {}).get("query") == "UPDATE TODO LIST"
            ):
                todo_nodes.append(node)
                todo_nodes_map[node["label"]] = node

        return todo_nodes, todo_nodes_map

    def _group_nodes_by_to_dos(
        self,
        diagram: dict[str, Any],
        to_do_nodes: list[dict[str, Any]],
        to_do_nodes_map: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Group nodes into segments based to-do update boundaries.

        Args:
            diagram: The full diagram
            to_do_nodes: List of to-do update nodes
            to_do_nodes_map: Map of todo node labels to nodes

        Returns:
            Tuple of (work_node_groups, extracted_todo_nodes) where:
            - work_node_groups: Groups containing only non-TODO work nodes
            - extracted_todo_nodes: TODO nodes in order for main diagram insertion
        """
        all_nodes = diagram.get("nodes", [])
        all_connections = diagram.get("connections", [])

        # Create position-based ordering of nodes
        node_positions = {}
        for i, node in enumerate(all_nodes):
            # Use position for ordering, fallback to index
            pos = node.get("position", {})
            x, y = pos.get("x", i * 100), pos.get("y", 100)
            node_positions[node["label"]] = (x, y, i)

        # Sort nodes by position (left to right, top to bottom)
        sorted_nodes = sorted(all_nodes, key=lambda n: node_positions[n["label"]])

        # Find to-do node positions in sorted order
        to_do_positions = []
        extracted_todos = []

        for to_do_node in to_do_nodes:
            for i, node in enumerate(sorted_nodes):
                if node["label"] == to_do_node["label"]:
                    to_do_positions.append(i)
                    extracted_todos.append(node)  # Collect TODO nodes in order
                    break

        # Separate work nodes from TODO nodes
        if self.extract_todos_to_main:
            # Create groups using original segmentation but excluding TODO nodes
            groups = self._create_segmented_work_groups(
                sorted_nodes, to_do_positions, to_do_nodes_map, all_connections, diagram
            )
        else:
            # Original behavior: include TODO nodes in groups
            groups = self._create_original_groups(
                sorted_nodes, to_do_positions, all_connections, diagram
            )

        return groups, extracted_todos

    def _create_segmented_work_groups(
        self,
        sorted_nodes: list[dict[str, Any]],
        to_do_positions: list[int],
        to_do_nodes_map: dict[str, dict[str, Any]],
        all_connections: list[dict[str, Any]],
        diagram: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Create groups using original TODO-boundary segmentation but excluding TODO nodes."""
        groups = []
        start_idx = 0

        for i, to_do_pos in enumerate(to_do_positions):
            # Create group from start_idx to to_do_pos (inclusive) but filter out TODO nodes
            segment_nodes = sorted_nodes[start_idx : to_do_pos + 1]

            # Filter out TODO nodes from this segment
            work_nodes = [node for node in segment_nodes if node["label"] not in to_do_nodes_map]

            if work_nodes and len(work_nodes) >= self.min_nodes_for_subdiagram:
                group_name = "prev_to_do" if i == 0 else f"to_do_{i}"
                group = self._create_node_group(group_name, work_nodes, all_connections, diagram)
                groups.append(group)
            elif work_nodes and not self.skip_trivial_subdiagrams:
                # Include even small groups if not skipping trivial ones
                group_name = "prev_to_do" if i == 0 else f"to_do_{i}"
                group = self._create_node_group(group_name, work_nodes, all_connections, diagram)
                groups.append(group)

            start_idx = to_do_pos + 1

        # Handle remaining nodes after last to-do (filter out TODOs)
        if start_idx < len(sorted_nodes):
            remaining_nodes = sorted_nodes[start_idx:]
            work_nodes = [node for node in remaining_nodes if node["label"] not in to_do_nodes_map]

            if (work_nodes and len(work_nodes) >= self.min_nodes_for_subdiagram) or (
                work_nodes and not self.skip_trivial_subdiagrams
            ):
                group_name = f"to_do_{len(to_do_positions)}"
                group = self._create_node_group(group_name, work_nodes, all_connections, diagram)
                groups.append(group)

        return groups

    def _create_work_groups(
        self,
        work_nodes: list[dict[str, Any]],
        all_connections: list[dict[str, Any]],
        diagram: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Create groups from work nodes only, applying minimum size filtering."""
        if not work_nodes:
            return []

        # For now, create a single group of all work nodes
        # In a more sophisticated implementation, we could group by other criteria
        groups = []

        if len(work_nodes) >= self.min_nodes_for_subdiagram:
            group_name = "work_group_1"
            group = self._create_node_group(group_name, work_nodes, all_connections, diagram)
            groups.append(group)
        elif not self.skip_trivial_subdiagrams:
            # Include even small groups if not skipping trivial ones
            group_name = "work_group_1"
            group = self._create_node_group(group_name, work_nodes, all_connections, diagram)
            groups.append(group)

        return groups

    def _create_original_groups(
        self,
        sorted_nodes: list[dict[str, Any]],
        to_do_positions: list[int],
        all_connections: list[dict[str, Any]],
        diagram: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Create groups using the original algorithm (for backward compatibility)."""
        groups = []
        start_idx = 0

        for i, to_do_pos in enumerate(to_do_positions):
            # Create group from start_idx to to_do_pos (inclusive)
            group_nodes = sorted_nodes[start_idx : to_do_pos + 1]

            if group_nodes:
                group_name = "prev_to_do" if i == 0 else f"to_do_{i}"
                group = self._create_node_group(group_name, group_nodes, all_connections, diagram)
                groups.append(group)

            start_idx = to_do_pos + 1

        # Handle remaining nodes after last to-do
        if start_idx < len(sorted_nodes):
            remaining_nodes = sorted_nodes[start_idx:]
            if remaining_nodes:
                group_name = f"to_do_{len(to_do_positions)}"
                group = self._create_node_group(
                    group_name, remaining_nodes, all_connections, diagram
                )
                groups.append(group)

        return groups

    def _create_node_group(
        self,
        group_name: str,
        nodes: list[dict[str, Any]],
        all_connections: list[dict[str, Any]],
        original_diagram: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a node group with its contained nodes and relevant connections.

        Args:
            group_name: Name of the group
            nodes: Nodes in this group
            all_connections: All connections from original diagram
            original_diagram: Original diagram for metadata

        Returns:
            Dictionary representing the node group
        """
        node_labels = {node["label"] for node in nodes}

        # Find connections within this group
        internal_connections = []
        for conn in all_connections:
            if conn.get("from") in node_labels and conn.get("to") in node_labels:
                internal_connections.append(conn)

        # Create sub-diagram structure
        sub_diagram = {
            "version": "light",
            "nodes": nodes,
            "connections": internal_connections,
            "metadata": {
                "group_name": group_name,
                "node_count": len(nodes),
                "connection_count": len(internal_connections),
                "extracted_from": original_diagram.get("metadata", {}).get("session_id", "unknown"),
            },
        }

        # Copy persons if they exist in original
        if "persons" in original_diagram:
            sub_diagram["persons"] = original_diagram["persons"]

        return {"name": group_name, "sub_diagram": sub_diagram, "node_labels": node_labels}

    def _create_grouped_diagram(
        self,
        original_diagram: dict[str, Any],
        node_groups: list[dict[str, Any]],
        extracted_todos: list[dict[str, Any]],
        report: DiagramProcessingReport,
    ) -> dict[str, Any]:
        """
        Create the main grouped diagram with sub_diagram nodes and extracted TODO nodes.

        Args:
            original_diagram: Original diagram
            node_groups: List of node groups
            extracted_todos: List of extracted TODO nodes to insert between sub-diagrams
            report: Processing report

        Returns:
            New grouped diagram
        """
        # Create start node
        start_node = {
            "label": "Start",
            "type": "start",
            "position": {"x": 100, "y": 100},
            "props": {
                "trigger_mode": "manual",
                "custom_data": original_diagram.get("nodes", [{}])[0]
                .get("props", {})
                .get("custom_data", {}),
            },
        }

        # Build nodes and connections with interleaved TODOs
        grouped_nodes = [start_node]
        grouped_connections = []

        x_pos = 300
        y_pos = 100
        x_spacing = 200

        prev_label = "Start"

        # If we have extracted TODOs and want to insert them between sub-diagrams
        if self.extract_todos_to_main and extracted_todos:
            # Strategy: alternate between TODO nodes and sub-diagram nodes
            todo_index = 0

            for _i, group in enumerate(node_groups):
                # Insert TODO node(s) before the sub-diagram (except before the first one)
                if todo_index < len(extracted_todos):
                    todo_node = extracted_todos[todo_index].copy()
                    todo_node["position"] = {"x": x_pos, "y": y_pos}
                    grouped_nodes.append(todo_node)

                    # Connect from previous node to TODO
                    connection = {
                        "from": prev_label,
                        "to": todo_node["label"],
                        "content_type": "raw_text",
                    }
                    grouped_connections.append(connection)

                    prev_label = todo_node["label"]
                    x_pos += x_spacing
                    todo_index += 1

                # Create sub_diagram node
                sub_diagram_label = f"{group['name']}_sub"
                sub_node = {
                    "label": sub_diagram_label,
                    "type": "sub_diagram",
                    "position": {"x": x_pos, "y": y_pos},
                    "props": {
                        "sub_diagram_path": f"{self.output_subdirectory}/{group['name']}.light.yaml",
                        "execution_mode": "sequential",
                    },
                }

                grouped_nodes.append(sub_node)

                # Create connection from previous node to sub-diagram
                connection = {
                    "from": prev_label,
                    "to": sub_diagram_label,
                    "content_type": "raw_text",
                }
                grouped_connections.append(connection)

                # Save sub-diagram file
                self._save_sub_diagram(group, report)

                prev_label = sub_diagram_label
                x_pos += x_spacing

            # Add any remaining TODO nodes at the end
            while todo_index < len(extracted_todos):
                todo_node = extracted_todos[todo_index].copy()
                todo_node["position"] = {"x": x_pos, "y": y_pos}
                grouped_nodes.append(todo_node)

                # Connect from previous node to TODO
                connection = {
                    "from": prev_label,
                    "to": todo_node["label"],
                    "content_type": "raw_text",
                }
                grouped_connections.append(connection)

                prev_label = todo_node["label"]
                x_pos += x_spacing
                todo_index += 1

        else:
            # Original behavior: just sub-diagrams
            for _i, group in enumerate(node_groups):
                sub_diagram_label = f"{group['name']}_sub"

                # Create sub_diagram node
                sub_node = {
                    "label": sub_diagram_label,
                    "type": "sub_diagram",
                    "position": {"x": x_pos, "y": y_pos},
                    "props": {
                        "sub_diagram_path": f"{self.output_subdirectory}/{group['name']}.light.yaml",
                        "execution_mode": "sequential",
                    },
                }

                grouped_nodes.append(sub_node)

                # Create connection from previous node
                connection = {
                    "from": prev_label,
                    "to": sub_diagram_label,
                    "content_type": "raw_text",
                }
                grouped_connections.append(connection)

                # Save sub-diagram file
                self._save_sub_diagram(group, report)

                prev_label = sub_diagram_label
                x_pos += x_spacing

        # Create the grouped diagram
        grouped_diagram = {
            "version": "light",
            "nodes": grouped_nodes,
            "connections": grouped_connections,
            "metadata": {
                **original_diagram.get("metadata", {}),
                "grouped": True,
                "original_nodes": len(original_diagram.get("nodes", [])),
                "sub_diagrams": len(node_groups),
                "extracted_todos": len(extracted_todos) if self.extract_todos_to_main else 0,
                "grouping_method": "todo_updates_with_extraction"
                if self.extract_todos_to_main
                else "todo_updates",
            },
        }

        # Copy persons if they exist
        if "persons" in original_diagram:
            grouped_diagram["persons"] = original_diagram["persons"]

        return grouped_diagram

    def _create_linear_todo_flow(
        self,
        original_diagram: dict[str, Any],
        extracted_todos: list[dict[str, Any]],
        report: DiagramProcessingReport,
    ) -> dict[str, Any]:
        """
        Create a linear flow of TODO nodes when there are no meaningful work groups.

        Args:
            original_diagram: Original diagram
            extracted_todos: List of TODO nodes to chain together
            report: Processing report

        Returns:
            Linear diagram with just TODO updates
        """
        # Create start node
        start_node = {
            "label": "Start",
            "type": "start",
            "position": {"x": 100, "y": 100},
            "props": {
                "trigger_mode": "manual",
                "custom_data": original_diagram.get("nodes", [{}])[0]
                .get("props", {})
                .get("custom_data", {}),
            },
        }

        # Build linear chain of TODO nodes
        grouped_nodes = [start_node]
        grouped_connections = []

        x_pos = 300
        y_pos = 100
        x_spacing = 200

        prev_label = "Start"

        for _i, todo_node in enumerate(extracted_todos):
            # Copy TODO node and update position
            linear_todo = todo_node.copy()
            linear_todo["position"] = {"x": x_pos, "y": y_pos}
            grouped_nodes.append(linear_todo)

            # Connect from previous node
            connection = {
                "from": prev_label,
                "to": linear_todo["label"],
                "content_type": "raw_text",
            }
            grouped_connections.append(connection)

            prev_label = linear_todo["label"]
            x_pos += x_spacing

        # Create the linear diagram
        linear_diagram = {
            "version": "light",
            "nodes": grouped_nodes,
            "connections": grouped_connections,
            "metadata": {
                **original_diagram.get("metadata", {}),
                "grouped": True,
                "linear_todo_flow": True,
                "original_nodes": len(original_diagram.get("nodes", [])),
                "todo_nodes": len(extracted_todos),
                "grouping_method": "linear_todo_flow",
            },
        }

        # Copy persons if they exist
        if "persons" in original_diagram:
            linear_diagram["persons"] = original_diagram["persons"]

        report.add_change(
            DiagramChange(
                change_type=DiagramChangeType.METADATA_UPDATED,
                description=f"Created linear TODO flow with {len(extracted_todos)} TODO nodes",
                target="linear_flow",
                details={"todo_nodes": len(extracted_todos), "flow_type": "linear"},
            )
        )

        return linear_diagram

    def _save_sub_diagram(self, group: dict[str, Any], report: DiagramProcessingReport) -> None:
        """
        Save a sub-diagram to file.

        Args:
            group: Node group containing sub-diagram data
            report: Processing report to update
        """
        try:
            # Get output base path from config, default to current directory
            output_base = self.config.get("output_base_path", ".")
            output_dir = Path(output_base) / self.output_subdirectory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save sub-diagram file
            file_path = output_dir / f"{group['name']}.light.yaml"

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    group["sub_diagram"],
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=4096,
                )

            report.add_change(
                DiagramChange(
                    change_type=DiagramChangeType.METADATA_UPDATED,
                    description=f"Created sub-diagram file: {file_path}",
                    target=str(file_path),
                    details={
                        "nodes": len(group["sub_diagram"]["nodes"]),
                        "connections": len(group["sub_diagram"]["connections"]),
                    },
                )
            )

        except Exception as e:
            report.add_change(
                DiagramChange(
                    change_type=DiagramChangeType.METADATA_UPDATED,
                    description=f"Failed to save sub-diagram {group['name']}: {e}",
                    target=group["name"],
                    details={"error": str(e)},
                )
            )

    def is_applicable(self, diagram: dict[str, Any]) -> bool:
        """
        Check if this processor is applicable to the given diagram.

        Args:
            diagram: The diagram to check

        Returns:
            True if the diagram has to-do update nodes
        """
        if not super().is_applicable(diagram):
            return False

        # Must have at least one to-do update node
        to_do_nodes, _ = self._find_to_do_update_nodes(diagram.get("nodes", []))
        return len(to_do_nodes) > 0
