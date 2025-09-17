"""TodoTranslator service for converting TodoSnapshot to Light diagrams."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dipeo.domain.diagram.models.format_models import (
    LightConnection,
    LightDiagram,
    LightNode,
)

logger = logging.getLogger(__name__)


class TodoTranslator:
    """Translates TodoSnapshot instances into Light format diagrams."""

    # Layout configuration
    LAYOUT_CONFIG = {
        "column_width": 300,  # Width between status columns
        "row_height": 120,  # Height between tasks in same column
        "start_x": 100,  # Starting X position
        "start_y": 100,  # Starting Y position
        "column_spacing": 400,  # Spacing between columns
    }

    # Status visual mapping (for metadata)
    STATUS_VISUAL_MAP = {
        "pending": {
            "color": "#FFA500",  # Orange
            "icon": "⏳",
            "badge": "TODO",
            "column": 0,
        },
        "in_progress": {
            "color": "#1E90FF",  # Blue
            "icon": "🔄",
            "badge": "WIP",
            "column": 1,
        },
        "completed": {
            "color": "#32CD32",  # Green
            "icon": "✅",
            "badge": "DONE",
            "column": 2,
        },
    }

    def __init__(self):
        """Initialize the TodoTranslator."""
        self._node_counter = 0

    def translate(
        self,
        todo_snapshot: Any,  # TodoSnapshot type from collector
        diagram_id: str | None = None,
        include_metadata: bool = True,
    ) -> LightDiagram:
        """
        Translate a TodoSnapshot into a Light format diagram.

        Args:
            todo_snapshot: The TodoSnapshot to translate
            diagram_id: Optional diagram ID (auto-generated if not provided)
            include_metadata: Whether to include metadata in the diagram

        Returns:
            LightDiagram representing the TODO items
        """
        if not diagram_id:
            diagram_id = f"todo_{todo_snapshot.session_id}_{uuid.uuid4().hex[:8]}"

        logger.info(f"[TodoTranslator] Translating snapshot with {len(todo_snapshot.todos)} todos")

        # Group todos by status for layout
        grouped_todos = self._group_by_status(todo_snapshot.todos)

        # Create nodes for each TODO item
        nodes = []
        connections = []
        node_mapping = {}  # Map todo index to node label

        # Add start node
        start_label = "todo_start"
        nodes.append(
            LightNode(
                type="start",
                label=start_label,
                position={"x": self.LAYOUT_CONFIG["start_x"] - 50, "y": 50},
            )
        )

        # Create nodes for each TODO
        for status, todos in grouped_todos.items():
            column_config = self.STATUS_VISUAL_MAP.get(status, {})
            column_index = column_config.get("column", 0)

            for row_index, todo in enumerate(todos):
                node_label = self._generate_node_label(todo, status)
                node_position = self._calculate_position(column_index, row_index)

                # Create a note node for each TODO item
                node = LightNode(
                    type="note",
                    label=node_label,
                    position=node_position,
                    # Store TODO details in props
                    content=todo.content,
                    status=status,
                    active_form=todo.active_form,
                    todo_index=todo.index,
                    visual_config=column_config,
                )

                nodes.append(node)
                node_mapping[todo.index] = node_label

                # Connect from start to first pending tasks
                if status == "pending" and row_index == 0:
                    connections.append(
                        LightConnection(
                            **{"from": start_label, "to": node_label, "label": "Initialize"}
                        )
                    )

        # Create logical flow connections between status groups
        self._add_status_flow_connections(connections, grouped_todos, node_mapping)

        # Add endpoint node for completed tasks
        if grouped_todos.get("completed"):
            endpoint_label = "todo_complete"
            nodes.append(
                LightNode(
                    type="endpoint",
                    label=endpoint_label,
                    position={
                        "x": self.LAYOUT_CONFIG["start_x"]
                        + self.LAYOUT_CONFIG["column_spacing"] * 3,
                        "y": self.LAYOUT_CONFIG["start_y"],
                    },
                )
            )

            # Connect completed tasks to endpoint
            for todo in grouped_todos["completed"]:
                if todo.index in node_mapping:
                    connections.append(
                        LightConnection(
                            **{
                                "from": node_mapping[todo.index],
                                "to": endpoint_label,
                                "label": "Complete",
                            }
                        )
                    )

        # Build metadata if requested
        metadata = None
        if include_metadata:
            metadata = self._build_metadata(todo_snapshot, diagram_id)

        # Create the Light diagram
        diagram = LightDiagram(
            nodes=nodes,
            connections=connections,
            metadata=metadata,
        )

        logger.debug(
            f"[TodoTranslator] Created diagram with {len(nodes)} nodes, "
            f"{len(connections)} connections"
        )

        return diagram

    def _group_by_status(self, todos: list) -> dict[str, list]:
        """Group TODO items by their status."""
        grouped = {"pending": [], "in_progress": [], "completed": []}

        for todo in todos:
            status = todo.status
            if status in grouped:
                grouped[status].append(todo)
            else:
                # Handle unknown status
                logger.warning(f"Unknown TODO status: {status}")
                grouped["pending"].append(todo)

        return grouped

    def _generate_node_label(self, todo: Any, status: str) -> str:
        """Generate a unique label for a TODO node."""
        self._node_counter += 1
        # Use a shortened version of the content for the label
        content_preview = (todo.content[:20] + "...") if len(todo.content) > 20 else todo.content
        # Remove spaces and special chars for valid label
        safe_content = "".join(c for c in content_preview if c.isalnum() or c in "_-")
        return f"todo_{status}_{self._node_counter}_{safe_content}"

    def _calculate_position(self, column_index: int, row_index: int) -> dict[str, int]:
        """Calculate the position for a node based on column and row."""
        x = self.LAYOUT_CONFIG["start_x"] + (column_index * self.LAYOUT_CONFIG["column_spacing"])
        y = self.LAYOUT_CONFIG["start_y"] + (row_index * self.LAYOUT_CONFIG["row_height"])
        return {"x": x, "y": y}

    def _add_status_flow_connections(
        self,
        connections: list,
        grouped_todos: dict[str, list],
        node_mapping: dict[int, str],
    ):
        """Add connections to show flow between status groups."""
        # Connect pending to in_progress
        if grouped_todos.get("pending") and grouped_todos.get("in_progress"):
            # Connect first pending to first in_progress as example flow
            first_pending = grouped_todos["pending"][0]
            first_in_progress = grouped_todos["in_progress"][0]

            if first_pending.index in node_mapping and first_in_progress.index in node_mapping:
                connections.append(
                    LightConnection(
                        **{
                            "from": node_mapping[first_pending.index],
                            "to": node_mapping[first_in_progress.index],
                            "label": "Start Work",
                        }
                    )
                )

        # Connect in_progress to completed
        if grouped_todos.get("in_progress") and grouped_todos.get("completed"):
            first_in_progress = grouped_todos["in_progress"][0]
            first_completed = grouped_todos["completed"][0]

            if first_in_progress.index in node_mapping and first_completed.index in node_mapping:
                connections.append(
                    LightConnection(
                        **{
                            "from": node_mapping[first_in_progress.index],
                            "to": node_mapping[first_completed.index],
                            "label": "Complete",
                        }
                    )
                )

    def _build_metadata(self, todo_snapshot: Any, diagram_id: str) -> dict[str, Any]:
        """Build metadata for the diagram."""
        metadata = {
            "diagram_id": diagram_id,
            "source": "claude_code_todo",
            "session_id": todo_snapshot.session_id,
            "trace_id": todo_snapshot.trace_id,
            "generated_at": datetime.now().isoformat(),
            "snapshot_timestamp": todo_snapshot.timestamp.isoformat(),
            "todo_count": len(todo_snapshot.todos),
            "status_visual_map": self.STATUS_VISUAL_MAP,
            "layout_config": self.LAYOUT_CONFIG,
        }

        # Add hook artifact linkage if available
        if todo_snapshot.doc_path:
            metadata["doc_path"] = todo_snapshot.doc_path

        if todo_snapshot.hook_event_timestamp:
            metadata["hook_event_timestamp"] = todo_snapshot.hook_event_timestamp.isoformat()

        # Add status counts
        status_counts = {}
        for todo in todo_snapshot.todos:
            status = todo.status
            status_counts[status] = status_counts.get(status, 0) + 1
        metadata["status_counts"] = status_counts

        return metadata

    def save_to_file(
        self,
        diagram: LightDiagram,
        output_path: Path | str,
        format: str = "yaml",
    ) -> Path:
        """
        Save a Light diagram to a file.

        Args:
            diagram: The LightDiagram to save
            output_path: Path where to save the file
            format: Output format ('yaml' or 'json')

        Returns:
            Path to the saved file
        """
        import json

        import yaml

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for serialization
        diagram_dict = {
            "version": "light",
            "nodes": [node.model_dump(exclude_none=True) for node in diagram.nodes],
            "connections": [
                conn.model_dump(by_alias=True, exclude_none=True) for conn in diagram.connections
            ],
        }

        if diagram.metadata:
            diagram_dict["metadata"] = diagram.metadata

        # Write to file based on format
        if format == "yaml":
            with open(output_path, "w") as f:
                yaml.dump(diagram_dict, f, default_flow_style=False, sort_keys=False)
        else:  # json
            with open(output_path, "w") as f:
                json.dump(diagram_dict, f, indent=2)

        logger.info(f"[TodoTranslator] Saved diagram to {output_path}")
        return output_path


class TodoDiagramSerializer:
    """Helper class for serializing TODO diagrams to different formats."""

    @staticmethod
    def to_light_yaml(diagram: LightDiagram) -> str:
        """Convert a LightDiagram to YAML string."""
        import yaml

        diagram_dict = {
            "version": "light",
            "nodes": [node.model_dump(exclude_none=True) for node in diagram.nodes],
            "connections": [
                conn.model_dump(by_alias=True, exclude_none=True) for conn in diagram.connections
            ],
        }

        if diagram.metadata:
            diagram_dict["metadata"] = diagram.metadata

        return yaml.dump(diagram_dict, default_flow_style=False, sort_keys=False)

    @staticmethod
    def to_graphql_input(diagram: LightDiagram, name: str, description: str = "") -> dict:
        """
        Convert a LightDiagram to GraphQL CreateDiagram mutation input.

        Args:
            diagram: The LightDiagram to convert
            name: Name for the diagram
            description: Optional description

        Returns:
            Dict suitable for GraphQL CreateDiagram mutation
        """
        # This would need to be adapted based on the actual GraphQL schema
        return {
            "name": name,
            "description": description or "TODO diagram generated from Claude Code session",
            "content": TodoDiagramSerializer.to_light_yaml(diagram),
            "format": "light",
            "metadata": diagram.metadata,
        }
