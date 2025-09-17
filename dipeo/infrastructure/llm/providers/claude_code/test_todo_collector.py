"""Unit tests for TodoTaskCollector module."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from claude_code_sdk.types import HookContext

# Use absolute imports for standalone execution
try:
    from .todo_collector import TodoItem, TodoSnapshot, TodoTaskCollector
except ImportError:
    from todo_collector import TodoItem, TodoSnapshot, TodoTaskCollector


class TestTodoItem:
    """Tests for TodoItem class."""

    def test_todo_item_creation(self):
        """Test TodoItem creation with all fields."""
        todo = TodoItem(
            content="Implement feature X",
            status="pending",
            active_form="Implementing feature X",
            index=0,
        )

        assert todo.content == "Implement feature X"
        assert todo.status == "pending"
        assert todo.active_form == "Implementing feature X"
        assert todo.index == 0

    def test_todo_item_minimal(self):
        """Test TodoItem creation with minimal fields."""
        todo = TodoItem(content="Fix bug", status="in_progress")

        assert todo.content == "Fix bug"
        assert todo.status == "in_progress"
        assert todo.active_form is None
        assert todo.index is None


class TestTodoSnapshot:
    """Tests for TodoSnapshot class."""

    def test_snapshot_creation(self):
        """Test TodoSnapshot creation."""
        todos = [
            TodoItem("Task 1", "pending"),
            TodoItem("Task 2", "in_progress", "Working on Task 2"),
            TodoItem("Task 3", "completed"),
        ]

        snapshot = TodoSnapshot(
            session_id="test-session", trace_id="trace-123", todos=todos, doc_path="/path/to/doc.md"
        )

        assert snapshot.session_id == "test-session"
        assert snapshot.trace_id == "trace-123"
        assert len(snapshot.todos) == 3
        assert snapshot.doc_path == "/path/to/doc.md"

    def test_snapshot_to_dict(self):
        """Test TodoSnapshot serialization to dict."""
        todos = [
            TodoItem("Task 1", "pending", index=0),
            TodoItem("Task 2", "completed", "Completed Task 2", index=1),
        ]

        snapshot = TodoSnapshot(session_id="test-session", trace_id="trace-123", todos=todos)

        data = snapshot.to_dict()

        assert data["session_id"] == "test-session"
        assert data["trace_id"] == "trace-123"
        assert len(data["todos"]) == 2
        assert data["todos"][0] == {
            "content": "Task 1",
            "status": "pending",
            "active_form": None,
            "index": 0,
        }
        assert data["todos"][1] == {
            "content": "Task 2",
            "status": "completed",
            "active_form": "Completed Task 2",
            "index": 1,
        }

    def test_snapshot_from_dict(self):
        """Test TodoSnapshot deserialization from dict."""
        data = {
            "session_id": "test-session",
            "trace_id": "trace-123",
            "timestamp": datetime.now().isoformat(),
            "todos": [
                {"content": "Task 1", "status": "pending", "active_form": None, "index": 0},
                {
                    "content": "Task 2",
                    "status": "completed",
                    "active_form": "Completed Task 2",
                    "index": 1,
                },
            ],
            "doc_path": "/path/to/doc.md",
        }

        snapshot = TodoSnapshot.from_dict(data)

        assert snapshot.session_id == "test-session"
        assert snapshot.trace_id == "trace-123"
        assert len(snapshot.todos) == 2
        assert snapshot.todos[0].content == "Task 1"
        assert snapshot.todos[0].status == "pending"
        assert snapshot.todos[1].content == "Task 2"
        assert snapshot.todos[1].status == "completed"
        assert snapshot.doc_path == "/path/to/doc.md"


class TestTodoTaskCollector:
    """Tests for TodoTaskCollector class."""

    @pytest.mark.asyncio
    async def test_handle_todo_write_hook_valid(self, tmp_path):
        """Test handling valid TodoWrite hook payload."""
        # Create collector with temp path
        with patch.object(
            TodoTaskCollector, "_get_persistence_path", return_value=tmp_path / "todo.json"
        ):
            collector = TodoTaskCollector("test-session", "trace-123")

            # Create mock hook input (PostToolUse payload)
            input_data = {
                "input": {
                    "todos": [
                        {
                            "content": "Task 1",
                            "status": "pending",
                            "activeForm": "Working on Task 1",
                        },
                        {
                            "content": "Task 2",
                            "status": "in_progress",
                            "activeForm": "Processing Task 2",
                        },
                        {
                            "content": "Task 3",
                            "status": "completed",
                            "activeForm": "Finished Task 3",
                        },
                    ]
                },
                "doc_path": "/test/doc.md",
            }

            context = HookContext()

            # Handle the hook
            result = await collector.handle_todo_write_hook(input_data, "tool-123", context)

            # Check result
            assert result["decision"] is None  # Should not block
            assert "3 items" in result["systemMessage"]

            # Check snapshot was created
            assert collector.current_snapshot is not None
            assert len(collector.current_snapshot.todos) == 3
            assert collector.current_snapshot.todos[0].content == "Task 1"
            assert collector.current_snapshot.todos[0].status == "pending"
            assert collector.current_snapshot.todos[1].status == "in_progress"
            assert collector.current_snapshot.todos[2].status == "completed"

            # Check persistence
            persistence_file = tmp_path / "todo.json"
            assert persistence_file.exists()
            with open(persistence_file) as f:
                saved_data = json.load(f)
            assert len(saved_data["todos"]) == 3

    @pytest.mark.asyncio
    async def test_handle_todo_write_hook_empty(self, tmp_path):
        """Test handling empty TodoWrite hook payload."""
        with patch.object(
            TodoTaskCollector, "_get_persistence_path", return_value=tmp_path / "todo.json"
        ):
            collector = TodoTaskCollector("test-session")

            # Empty input
            input_data = {"input": {"todos": []}}

            context = HookContext()

            # Handle the hook
            result = await collector.handle_todo_write_hook(input_data, None, context)

            # Should handle gracefully
            assert result["decision"] is None

    @pytest.mark.asyncio
    async def test_handle_todo_write_hook_malformed(self, tmp_path):
        """Test handling malformed TodoWrite hook payload."""
        with patch.object(
            TodoTaskCollector, "_get_persistence_path", return_value=tmp_path / "todo.json"
        ):
            collector = TodoTaskCollector("test-session")

            # Malformed input (missing todos key)
            input_data = {"input": {"invalid": "data"}}

            context = HookContext()

            # Handle the hook - should not raise
            result = await collector.handle_todo_write_hook(input_data, None, context)

            # Should handle gracefully
            assert result["decision"] is None

    @pytest.mark.asyncio
    async def test_handle_todo_write_hook_error(self, tmp_path):
        """Test handling errors during TodoWrite hook processing."""
        with patch.object(
            TodoTaskCollector, "_get_persistence_path", return_value=tmp_path / "todo.json"
        ):
            collector = TodoTaskCollector("test-session")

            # Input that will cause an error
            input_data = {
                "input": {
                    "todos": "not_a_list"  # Invalid type
                }
            }

            context = HookContext()

            # Handle the hook - should not raise
            result = await collector.handle_todo_write_hook(input_data, None, context)

            # Should handle gracefully and not block
            assert result["decision"] is None
            assert "error" in result["systemMessage"].lower()

    @pytest.mark.asyncio
    async def test_persist_and_load_snapshot(self, tmp_path):
        """Test persisting and loading snapshots."""
        with patch.object(
            TodoTaskCollector, "_get_persistence_path", return_value=tmp_path / "todo.json"
        ):
            collector = TodoTaskCollector("test-session", "trace-123")

            # Create a snapshot
            todos = [TodoItem("Task 1", "pending"), TodoItem("Task 2", "completed")]
            collector.current_snapshot = TodoSnapshot(
                session_id="test-session", trace_id="trace-123", todos=todos
            )

            # Persist
            await collector.persist_snapshot()

            # Create new collector and load
            collector2 = TodoTaskCollector("test-session", "trace-123")
            loaded = await collector2.load_snapshot()

            assert loaded is not None
            assert loaded.session_id == "test-session"
            assert len(loaded.todos) == 2
            assert loaded.todos[0].content == "Task 1"
            assert loaded.todos[1].content == "Task 2"

    def test_create_hook_config(self):
        """Test creating hook configuration for Claude Code client."""
        collector = TodoTaskCollector("test-session")
        config = collector.create_hook_config()

        assert "PostToolUse" in config
        assert len(config["PostToolUse"]) == 1
        assert config["PostToolUse"][0]["matcher"] == "TodoWrite"
        assert len(config["PostToolUse"][0]["hooks"]) == 1
        assert callable(config["PostToolUse"][0]["hooks"][0])


def test_integration_with_mixed_statuses():
    """Test snapshot with mixed TODO statuses."""
    todos = [
        TodoItem("Design API", "completed"),
        TodoItem("Implement backend", "in_progress"),
        TodoItem("Write tests", "pending"),
        TodoItem("Deploy to staging", "pending"),
    ]

    snapshot = TodoSnapshot(session_id="integration-test", todos=todos)

    # Convert to dict and back
    data = snapshot.to_dict()
    restored = TodoSnapshot.from_dict(data)

    # Verify all statuses preserved
    statuses = [t.status for t in restored.todos]
    assert statuses == ["completed", "in_progress", "pending", "pending"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

    # Or run basic tests directly
    print("Running basic tests...")

    # Test TodoItem
    todo = TodoItem("Test task", "pending")
    assert todo.content == "Test task"
    print("✓ TodoItem test passed")

    # Test TodoSnapshot
    snapshot = TodoSnapshot(session_id="test", todos=[todo])
    assert len(snapshot.todos) == 1
    print("✓ TodoSnapshot test passed")

    # Test serialization
    data = snapshot.to_dict()
    restored = TodoSnapshot.from_dict(data)
    assert restored.session_id == "test"
    print("✓ Serialization test passed")

    print("\nAll basic tests passed!")
    print("\nFor full test suite, run: pytest test_todo_collector.py")
