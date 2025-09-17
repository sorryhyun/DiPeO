"""Unit tests for TodoTranslator service."""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from dipeo.domain.diagram.models.format_models import LightDiagram
from dipeo.domain.diagram.services.todo_translator import TodoDiagramSerializer, TodoTranslator


class TestTodoTranslator:
    """Test suite for TodoTranslator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.translator = TodoTranslator()
        self.mock_snapshot = self._create_mock_snapshot()

    def _create_mock_snapshot(self):
        """Create a mock TodoSnapshot for testing."""
        snapshot = MagicMock()
        snapshot.session_id = "test-session-123"
        snapshot.trace_id = "trace-456"
        snapshot.timestamp = datetime.now()
        snapshot.doc_path = "/path/to/doc.md"
        snapshot.hook_event_timestamp = datetime.now()

        # Create mock todos with different statuses
        todo1 = MagicMock()
        todo1.content = "Write unit tests"
        todo1.status = "completed"
        todo1.active_form = "Writing unit tests"
        todo1.index = 0

        todo2 = MagicMock()
        todo2.content = "Implement feature"
        todo2.status = "in_progress"
        todo2.active_form = "Implementing feature"
        todo2.index = 1

        todo3 = MagicMock()
        todo3.content = "Review code"
        todo3.status = "pending"
        todo3.active_form = None
        todo3.index = 2

        todo4 = MagicMock()
        todo4.content = "Deploy to production"
        todo4.status = "pending"
        todo4.active_form = None
        todo4.index = 3

        snapshot.todos = [todo1, todo2, todo3, todo4]
        return snapshot

    def test_translate_basic(self):
        """Test basic translation of TodoSnapshot to LightDiagram."""
        diagram = self.translator.translate(self.mock_snapshot)

        assert isinstance(diagram, LightDiagram)
        # Should have: 1 start + 4 todos + 1 endpoint = 6 nodes
        assert len(diagram.nodes) == 6
        assert len(diagram.connections) > 0

        # Check node types
        node_types = [node.type for node in diagram.nodes]
        assert "start" in node_types
        assert "endpoint" in node_types
        assert node_types.count("note") == 4  # 4 TODO items

    def test_translate_with_custom_diagram_id(self):
        """Test translation with custom diagram ID."""
        custom_id = "custom-diagram-123"
        diagram = self.translator.translate(self.mock_snapshot, diagram_id=custom_id)

        assert diagram.metadata["diagram_id"] == custom_id

    def test_translate_without_metadata(self):
        """Test translation without including metadata."""
        diagram = self.translator.translate(self.mock_snapshot, include_metadata=False)

        assert diagram.metadata is None

    def test_group_by_status(self):
        """Test grouping TODOs by status."""
        grouped = self.translator._group_by_status(self.mock_snapshot.todos)

        assert len(grouped["pending"]) == 2
        assert len(grouped["in_progress"]) == 1
        assert len(grouped["completed"]) == 1

    def test_generate_node_label(self):
        """Test node label generation."""
        todo = MagicMock()
        todo.content = "This is a very long task description that should be truncated"

        label = self.translator._generate_node_label(todo, "pending")

        assert label.startswith("todo_pending_")
        assert len(label) < 50  # Should be reasonably short

    def test_calculate_position(self):
        """Test position calculation for nodes."""
        # Test different column and row positions
        pos1 = self.translator._calculate_position(0, 0)
        assert pos1["x"] == self.translator.LAYOUT_CONFIG["start_x"]
        assert pos1["y"] == self.translator.LAYOUT_CONFIG["start_y"]

        pos2 = self.translator._calculate_position(1, 2)
        expected_x = (
            self.translator.LAYOUT_CONFIG["start_x"]
            + self.translator.LAYOUT_CONFIG["column_spacing"]
        )
        expected_y = (
            self.translator.LAYOUT_CONFIG["start_y"]
            + 2 * self.translator.LAYOUT_CONFIG["row_height"]
        )
        assert pos2["x"] == expected_x
        assert pos2["y"] == expected_y

    def test_build_metadata(self):
        """Test metadata building."""
        diagram_id = "test-diagram"
        metadata = self.translator._build_metadata(self.mock_snapshot, diagram_id)

        assert metadata["diagram_id"] == diagram_id
        assert metadata["source"] == "claude_code_todo"
        assert metadata["session_id"] == self.mock_snapshot.session_id
        assert metadata["trace_id"] == self.mock_snapshot.trace_id
        assert metadata["todo_count"] == len(self.mock_snapshot.todos)
        assert metadata["doc_path"] == self.mock_snapshot.doc_path
        assert "status_counts" in metadata
        assert metadata["status_counts"]["pending"] == 2
        assert metadata["status_counts"]["in_progress"] == 1
        assert metadata["status_counts"]["completed"] == 1

    def test_save_to_file_yaml(self):
        """Test saving diagram to YAML file."""
        diagram = self.translator.translate(self.mock_snapshot)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_diagram.light.yaml"
            saved_path = self.translator.save_to_file(diagram, output_path, format="yaml")

            assert saved_path.exists()

            # Load and verify YAML content
            with open(saved_path) as f:
                loaded = yaml.safe_load(f)

            assert loaded["version"] == "light"
            assert len(loaded["nodes"]) == 6
            assert len(loaded["connections"]) > 0
            assert "metadata" in loaded

    def test_save_to_file_json(self):
        """Test saving diagram to JSON file."""
        diagram = self.translator.translate(self.mock_snapshot)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_diagram.json"
            saved_path = self.translator.save_to_file(diagram, output_path, format="json")

            assert saved_path.exists()

            # Load and verify JSON content
            with open(saved_path) as f:
                loaded = json.load(f)

            assert loaded["version"] == "light"
            assert len(loaded["nodes"]) == 6

    def test_empty_snapshot(self):
        """Test handling of empty TODO snapshot."""
        empty_snapshot = MagicMock()
        empty_snapshot.session_id = "empty-session"
        empty_snapshot.trace_id = None
        empty_snapshot.timestamp = datetime.now()
        empty_snapshot.todos = []
        empty_snapshot.doc_path = None
        empty_snapshot.hook_event_timestamp = None

        diagram = self.translator.translate(empty_snapshot)

        # Should still have start node
        assert len(diagram.nodes) >= 1
        assert any(node.type == "start" for node in diagram.nodes)

    def test_unknown_status_handling(self):
        """Test handling of TODOs with unknown status."""
        snapshot = MagicMock()
        snapshot.session_id = "test-session"
        snapshot.trace_id = None
        snapshot.timestamp = datetime.now()
        snapshot.todos = []
        snapshot.doc_path = None
        snapshot.hook_event_timestamp = None

        # Add todo with unknown status
        todo = MagicMock()
        todo.content = "Unknown task"
        todo.status = "unknown_status"
        todo.active_form = None
        todo.index = 0
        snapshot.todos = [todo]

        with patch("dipeo.domain.diagram.services.todo_translator.logger") as mock_logger:
            diagram = self.translator.translate(snapshot)

            # Should log warning about unknown status
            mock_logger.warning.assert_called_once()

            # Unknown status should be treated as pending
            assert len(diagram.nodes) > 1  # At least start + todo node


class TestTodoDiagramSerializer:
    """Test suite for TodoDiagramSerializer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.serializer = TodoDiagramSerializer()
        self.translator = TodoTranslator()
        self.mock_snapshot = self._create_mock_snapshot()

    def _create_mock_snapshot(self):
        """Create a mock TodoSnapshot for testing."""
        snapshot = MagicMock()
        snapshot.session_id = "test-session"
        snapshot.trace_id = "trace-123"
        snapshot.timestamp = datetime.now()
        snapshot.todos = []
        snapshot.doc_path = None
        snapshot.hook_event_timestamp = None

        todo = MagicMock()
        todo.content = "Test task"
        todo.status = "pending"
        todo.active_form = None
        todo.index = 0
        snapshot.todos = [todo]

        return snapshot

    def test_to_light_yaml(self):
        """Test converting diagram to YAML string."""
        diagram = self.translator.translate(self.mock_snapshot)
        yaml_str = self.serializer.to_light_yaml(diagram)

        assert isinstance(yaml_str, str)
        assert "version: light" in yaml_str
        assert "nodes:" in yaml_str
        assert "connections:" in yaml_str

        # Parse YAML to verify structure
        parsed = yaml.safe_load(yaml_str)
        assert parsed["version"] == "light"
        assert isinstance(parsed["nodes"], list)
        assert isinstance(parsed["connections"], list)

    def test_to_graphql_input(self):
        """Test converting diagram to GraphQL input."""
        diagram = self.translator.translate(self.mock_snapshot)
        name = "Test TODO Diagram"
        description = "Test description"

        graphql_input = self.serializer.to_graphql_input(diagram, name, description)

        assert graphql_input["name"] == name
        assert graphql_input["description"] == description
        assert graphql_input["format"] == "light"
        assert "content" in graphql_input
        assert "metadata" in graphql_input

        # Content should be valid YAML
        content_parsed = yaml.safe_load(graphql_input["content"])
        assert content_parsed["version"] == "light"

    def test_to_graphql_input_without_description(self):
        """Test GraphQL input generation without description."""
        diagram = self.translator.translate(self.mock_snapshot)
        name = "Test Diagram"

        graphql_input = self.serializer.to_graphql_input(diagram, name)

        assert graphql_input["name"] == name
        assert graphql_input["description"].startswith("TODO diagram generated")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
