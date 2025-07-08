"""Tests for the hook system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dipeo_cli.hooks import (
    Hook,
    HookEvent,
    HookObserver,
    HookRegistry,
    HookType,
)


@pytest.fixture
def temp_hooks_dir():
    """Create a temporary hooks directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def hook_registry(temp_hooks_dir):
    """Create a HookRegistry with temporary directory."""
    return HookRegistry(temp_hooks_dir)


class TestHookRegistry:
    """Test HookRegistry functionality."""

    def test_add_hook(self, hook_registry):
        """Test adding a hook."""
        hook = Hook(
            name="test_hook",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/path/to/script.sh",
        )

        assert hook_registry.add_hook(hook) is True
        assert len(hook_registry.hooks) == 1
        assert hook_registry.get_hook("test_hook") == hook

    def test_add_duplicate_hook(self, hook_registry):
        """Test adding duplicate hook fails."""
        hook = Hook(
            name="test_hook",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/path/to/script.sh",
        )

        assert hook_registry.add_hook(hook) is True
        assert hook_registry.add_hook(hook) is False
        assert len(hook_registry.hooks) == 1

    def test_remove_hook(self, hook_registry):
        """Test removing a hook."""
        hook = Hook(
            name="test_hook",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/path/to/script.sh",
        )

        hook_registry.add_hook(hook)
        assert hook_registry.remove_hook("test_hook") is True
        assert len(hook_registry.hooks) == 0
        assert hook_registry.get_hook("test_hook") is None

    def test_enable_disable_hook(self, hook_registry):
        """Test enabling and disabling hooks."""
        hook = Hook(
            name="test_hook",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/path/to/script.sh",
            enabled=True,
        )

        hook_registry.add_hook(hook)

        # Disable
        assert hook_registry.disable_hook("test_hook") is True
        assert hook_registry.get_hook("test_hook").enabled is False

        # Enable
        assert hook_registry.enable_hook("test_hook") is True
        assert hook_registry.get_hook("test_hook").enabled is True

    def test_get_hooks_for_event(self, hook_registry):
        """Test getting hooks for specific events."""
        hook1 = Hook(
            name="hook1",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/script1.sh",
        )
        hook2 = Hook(
            name="hook2",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/script2.sh",
        )
        hook3 = Hook(
            name="hook3",
            type=HookType.SHELL,
            event=HookEvent.EXECUTION_START,
            target="/script3.sh",
        )

        hook_registry.add_hook(hook1)
        hook_registry.add_hook(hook2)
        hook_registry.add_hook(hook3)

        node_hooks = hook_registry.get_hooks_for_event(HookEvent.NODE_COMPLETE)
        assert len(node_hooks) == 2
        assert hook1 in node_hooks
        assert hook2 in node_hooks

        exec_hooks = hook_registry.get_hooks_for_event(HookEvent.EXECUTION_START)
        assert len(exec_hooks) == 1
        assert hook3 in exec_hooks

    def test_persistence(self, temp_hooks_dir):
        """Test hook persistence across registry instances."""
        # Create and save hooks
        registry1 = HookRegistry(temp_hooks_dir)
        hook = Hook(
            name="persistent_hook",
            type=HookType.WEBHOOK,
            event=HookEvent.EXECUTION_COMPLETE,
            target="https://example.com/webhook",
        )
        registry1.add_hook(hook)

        # Load in new registry
        registry2 = HookRegistry(temp_hooks_dir)
        loaded_hook = registry2.get_hook("persistent_hook")

        assert loaded_hook is not None
        assert loaded_hook.name == hook.name
        assert loaded_hook.type == hook.type
        assert loaded_hook.event == hook.event
        assert loaded_hook.target == hook.target


class TestHookFilters:
    """Test hook filtering functionality."""

    def test_simple_filter_match(self):
        """Test simple equality filter."""
        hook = Hook(
            name="test",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/script.sh",
            filters={"node_type": "person_job"},
        )

        event_data = {"node_type": "person_job", "node_id": "123"}
        assert hook.matches_filters(event_data) is True

        event_data = {"node_type": "condition", "node_id": "123"}
        assert hook.matches_filters(event_data) is False

    def test_regex_filter(self):
        """Test regex pattern filter."""
        hook = Hook(
            name="test",
            type=HookType.SHELL,
            event=HookEvent.NODE_ERROR,
            target="/script.sh",
            filters={"error": "/.*timeout.*/"},
        )

        event_data = {"error": "Connection timeout after 30s"}
        assert hook.matches_filters(event_data) is True

        event_data = {"error": "Invalid input"}
        assert hook.matches_filters(event_data) is False

    def test_list_filter(self):
        """Test list inclusion filter."""
        hook = Hook(
            name="test",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/script.sh",
            filters={"node_id": ["node1", "node2", "node3"]},
        )

        event_data = {"node_id": "node2"}
        assert hook.matches_filters(event_data) is True

        event_data = {"node_id": "node4"}
        assert hook.matches_filters(event_data) is False

    def test_wildcard_filter(self):
        """Test wildcard pattern filter."""
        hook = Hook(
            name="test",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target="/script.sh",
            filters={"node_id": "person_*"},
        )

        event_data = {"node_id": "person_123"}
        assert hook.matches_filters(event_data) is True

        event_data = {"node_id": "condition_456"}
        assert hook.matches_filters(event_data) is False


class TestHookObserver:
    """Test HookObserver functionality."""

    @pytest.mark.asyncio
    async def test_shell_hook_execution(self, temp_hooks_dir):
        """Test shell hook execution."""
        # Create a test script
        script_path = temp_hooks_dir / "test_script.sh"
        script_path.write_text("#!/bin/bash\necho $DIPEO_EVENT > output.txt")
        script_path.chmod(0o755)

        # Create hook
        hook = Hook(
            name="test",
            type=HookType.SHELL,
            event=HookEvent.NODE_COMPLETE,
            target=str(script_path),
        )

        registry = HookRegistry(temp_hooks_dir)
        registry.add_hook(hook)

        observer = HookObserver(registry)

        # Mock output for testing
        output_mock = MagicMock()
        output_mock.model_dump.return_value = {"result": "test"}

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock the subprocess
            process_mock = AsyncMock()
            process_mock.communicate.return_value = (b"", b"")
            process_mock.returncode = 0
            mock_subprocess.return_value = process_mock

            await observer.on_node_complete("exec123", "node456", output_mock)

            # Verify subprocess was called
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0]
            assert str(script_path) in call_args

    @pytest.mark.asyncio
    async def test_webhook_hook_execution(self, temp_hooks_dir):
        """Test webhook hook execution."""
        hook = Hook(
            name="test",
            type=HookType.WEBHOOK,
            event=HookEvent.EXECUTION_COMPLETE,
            target="https://example.com/webhook",
        )

        registry = HookRegistry(temp_hooks_dir)
        registry.add_hook(hook)

        observer = HookObserver(registry)

        with patch("aiohttp.ClientSession.post") as mock_post:
            # Mock the HTTP response
            response_mock = AsyncMock()
            response_mock.status = 200
            mock_post.return_value.__aenter__.return_value = response_mock

            await observer.on_execution_complete("exec123")

            # Verify webhook was called
            mock_post.assert_called_once()
            assert mock_post.call_args[0][0] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_file_hook_execution(self, temp_hooks_dir):
        """Test file hook execution."""
        output_file = temp_hooks_dir / "events.jsonl"

        hook = Hook(
            name="test",
            type=HookType.FILE,
            event=HookEvent.EXECUTION_START,
            target=str(output_file),
        )

        registry = HookRegistry(temp_hooks_dir)
        registry.add_hook(hook)

        observer = HookObserver(registry)
        await observer.on_execution_start("exec123", "diagram456")

        # Verify file was written
        assert output_file.exists()

        # Check content
        with open(output_file) as f:
            data = json.loads(f.readline())
            assert data["event"] == HookEvent.EXECUTION_START.value
            assert data["data"]["execution_id"] == "exec123"
            assert data["data"]["diagram_name"] == "diagram456"

    @pytest.mark.asyncio
    async def test_disabled_hook_not_executed(self, temp_hooks_dir):
        """Test that disabled hooks are not executed."""
        hook = Hook(
            name="test",
            type=HookType.FILE,
            event=HookEvent.EXECUTION_START,
            target=str(temp_hooks_dir / "events.jsonl"),
            enabled=False,
        )

        registry = HookRegistry(temp_hooks_dir)
        registry.add_hook(hook)

        observer = HookObserver(registry)
        await observer.on_execution_start("exec123", "diagram456")

        # Verify file was NOT written
        assert not (temp_hooks_dir / "events.jsonl").exists()
