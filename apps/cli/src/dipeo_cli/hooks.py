"""Hook system for DiPeO - Execute external scripts/commands on diagram events."""

import json
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiohttp
import sys

from dipeo.domain.services.execution.protocols import ExecutionObserver
from dipeo.models import NodeOutput

logger = logging.getLogger(__name__)


class HookType(str, Enum):
    """Types of hooks supported."""

    SHELL = "shell"
    WEBHOOK = "webhook"
    PYTHON = "python"
    FILE = "file"


class HookEvent(str, Enum):
    """Events that can trigger hooks."""

    EXECUTION_START = "execution_start"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_ERROR = "execution_error"
    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"
    NODE_ERROR = "node_error"


@dataclass
class Hook:
    """Hook configuration."""

    name: str
    type: HookType
    event: HookEvent
    target: str  # Script path, URL, or file path
    enabled: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def matches_filters(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data matches hook filters."""
        if not self.filters:
            return True

        for key, expected_value in self.filters.items():
            if key not in event_data:
                return False

            actual_value = event_data[key]

            # Support regex patterns
            if (
                isinstance(expected_value, str)
                and expected_value.startswith("/")
                and expected_value.endswith("/")
            ):
                import re

                pattern = expected_value[1:-1]
                if not re.match(pattern, str(actual_value)):
                    return False
            # Support list inclusion
            elif isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            # Simple equality
            elif actual_value != expected_value:
                return False

        return True


class HookRegistry:
    """Registry for managing hooks."""

    def __init__(self, hooks_dir: Optional[Path] = None):
        if hooks_dir is None:
            hooks_dir = Path("files/hooks")
        self.hooks_dir = hooks_dir
        self.hooks_file = hooks_dir / "hooks.json"
        self.hooks: List[Hook] = []
        self._load_hooks()

    def _load_hooks(self):
        """Load hooks from storage."""
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        if self.hooks_file.exists():
            try:
                with open(self.hooks_file) as f:
                    hooks_data = json.load(f)
                    self.hooks = [Hook(**hook_data) for hook_data in hooks_data]
            except Exception as e:
                logger.error(f"Failed to load hooks: {e}")
                self.hooks = []
        else:
            self.hooks = []
            self._save_hooks()

    def _save_hooks(self):
        """Save hooks to storage."""
        hooks_data = [asdict(hook) for hook in self.hooks]
        with open(self.hooks_file, "w") as f:
            json.dump(hooks_data, f, indent=2)

    def add_hook(self, hook: Hook) -> bool:
        """Add a new hook."""
        # Check for duplicate names
        if any(h.name == hook.name for h in self.hooks):
            return False

        self.hooks.append(hook)
        self._save_hooks()
        return True

    def remove_hook(self, name: str) -> bool:
        """Remove a hook by name."""
        initial_count = len(self.hooks)
        self.hooks = [h for h in self.hooks if h.name != name]

        if len(self.hooks) < initial_count:
            self._save_hooks()
            return True
        return False

    def get_hook(self, name: str) -> Optional[Hook]:
        """Get a hook by name."""
        for hook in self.hooks:
            if hook.name == name:
                return hook
        return None

    def get_hooks_for_event(self, event: HookEvent) -> List[Hook]:
        """Get all enabled hooks for a specific event."""
        return [h for h in self.hooks if h.enabled and h.event == event]

    def list_hooks(self) -> List[Hook]:
        """Get all registered hooks."""
        return self.hooks.copy()

    def enable_hook(self, name: str) -> bool:
        """Enable a hook."""
        hook = self.get_hook(name)
        if hook:
            hook.enabled = True
            self._save_hooks()
            return True
        return False

    def disable_hook(self, name: str) -> bool:
        """Disable a hook."""
        hook = self.get_hook(name)
        if hook:
            hook.enabled = False
            self._save_hooks()
            return True
        return False


class HookObserver(ExecutionObserver):
    """Observer that executes hooks on diagram events."""

    def __init__(self, hook_registry: HookRegistry):
        self.hook_registry = hook_registry
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def _execute_hook(self, hook: Hook, event_data: Dict[str, Any]):
        """Execute a hook with event data."""
        try:
            if not hook.matches_filters(event_data):
                return

            # Execute hook silently unless there's an error

            if hook.type == HookType.SHELL:
                await self._execute_shell_hook(hook, event_data)
            elif hook.type == HookType.WEBHOOK:
                await self._execute_webhook_hook(hook, event_data)
            elif hook.type == HookType.PYTHON:
                await self._execute_python_hook(hook, event_data)
            elif hook.type == HookType.FILE:
                await self._execute_file_hook(hook, event_data)

        except Exception as e:
            logger.error(f"Failed to execute hook '{hook.name}': {e}")

    async def _execute_shell_hook(self, hook: Hook, event_data: Dict[str, Any]):
        """Execute a shell script hook."""
        script_path = Path(hook.target)
        if not script_path.is_absolute():
            script_path = self.hook_registry.hooks_dir / script_path

        if not script_path.exists():
            logger.error(f"Shell script not found: {script_path}")
            return

        # Pass event data as environment variables
        env = dict(os.environ)
        env["DIPEO_EVENT"] = hook.event
        env["DIPEO_EVENT_DATA"] = json.dumps(event_data)

        # Also pass flattened environment variables
        for key, value in self._flatten_dict(event_data):
            env_key = f"DIPEO_{key.upper().replace('.', '_')}"
            env[env_key] = str(value)

        timeout = hook.options.get("timeout", 30)

        process = await asyncio.create_subprocess_exec(
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode != 0:
                logger.error(f"Hook script failed: {stderr.decode()}")

        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"Hook script timed out after {timeout}s")

    async def _execute_webhook_hook(self, hook: Hook, event_data: Dict[str, Any]):
        """Execute a webhook hook."""
        await self._ensure_session()

        url = hook.target
        headers = hook.options.get("headers", {})
        timeout = hook.options.get("timeout", 10)

        payload = {"event": hook.event, "data": event_data, "hook_name": hook.name}

        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status >= 400:
                    logger.error(f"Webhook failed with status {response.status}")

        except Exception as e:
            logger.error(f"Webhook request failed: {e}")

    async def _execute_python_hook(self, hook: Hook, event_data: Dict[str, Any]):
        """Execute a Python script hook."""
        script_path = Path(hook.target)
        if not script_path.is_absolute():
            script_path = self.hook_registry.hooks_dir / script_path

        if not script_path.exists():
            logger.error(f"Python script not found: {script_path}")
            return

        # Execute Python script in subprocess
        timeout = hook.options.get("timeout", 30)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # Send event data as JSON to stdin
            event_json = json.dumps({"event": hook.event, "data": event_data})

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=event_json.encode()), timeout=timeout
            )

            if process.returncode != 0:
                logger.error(f"Python hook failed: {stderr.decode()}")

        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"Python hook timed out after {timeout}s")

    async def _execute_file_hook(self, hook: Hook, event_data: Dict[str, Any]):
        """Write event data to a file."""
        file_path = Path(hook.target)
        if not file_path.is_absolute():
            file_path = self.hook_registry.hooks_dir / file_path

        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data to write
        data = {
            "event": hook.event,
            "timestamp": event_data.get("timestamp", ""),
            "data": event_data,
        }

        # Append to file
        mode = hook.options.get("mode", "append")
        write_mode = "a" if mode == "append" else "w"

        with open(file_path, write_mode) as f:
            f.write(json.dumps(data) + "\n")

    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> List[tuple]:
        """Flatten nested dictionary for environment variables."""
        items = []

        for key, value in d.items():
            new_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key))
            elif isinstance(value, (list, tuple)):
                items.append((f"{new_key}_count", len(value)))
                for i, item in enumerate(value):
                    items.append((f"{new_key}_{i}", item))
            else:
                items.append((new_key, value))

        return items

    # ExecutionObserver implementation
    async def on_execution_start(self, execution_id: str, diagram_name: str):
        """Handle execution start event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.EXECUTION_START)

        event_data = {
            "execution_id": execution_id,
            "diagram_name": diagram_name,
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def on_node_start(self, execution_id: str, node_id: str):
        """Handle node start event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.NODE_START)

        event_data = {
            "execution_id": execution_id,
            "node_id": node_id,
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def on_node_complete(
        self, execution_id: str, node_id: str, output: NodeOutput
    ):
        """Handle node complete event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.NODE_COMPLETE)

        event_data = {
            "execution_id": execution_id,
            "node_id": node_id,
            "output": output.model_dump() if output else {},
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        """Handle node error event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.NODE_ERROR)

        event_data = {
            "execution_id": execution_id,
            "node_id": node_id,
            "error": error,
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def on_execution_complete(self, execution_id: str):
        """Handle execution complete event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.EXECUTION_COMPLETE)

        event_data = {
            "execution_id": execution_id,
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def on_execution_error(self, execution_id: str, error: str):
        """Handle execution error event."""
        hooks = self.hook_registry.get_hooks_for_event(HookEvent.EXECUTION_ERROR)

        event_data = {
            "execution_id": execution_id,
            "error": error,
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        for hook in hooks:
            await self._execute_hook(hook, event_data)

    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None


# CLI Commands
def hook_list_command(args):
    """List all registered hooks."""
    registry = HookRegistry()
    hooks = registry.list_hooks()

    if not hooks:
        print("No hooks registered.")
        return

    print(f"{'Name':<20} {'Type':<10} {'Event':<20} {'Enabled':<8} {'Target'}")
    print("-" * 80)

    for hook in hooks:
        enabled = "Yes" if hook.enabled else "No"
        print(
            f"{hook.name:<20} {hook.type:<10} {hook.event:<20} {enabled:<8} {hook.target}"
        )


def hook_add_command(args):
    """Add a new hook."""
    import argparse

    parser = argparse.ArgumentParser(prog="dipeo hook add")
    parser.add_argument("name", help="Hook name")
    parser.add_argument("type", choices=[t.value for t in HookType], help="Hook type")
    parser.add_argument(
        "event", choices=[e.value for e in HookEvent], help="Event to trigger on"
    )
    parser.add_argument("target", help="Script path, URL, or file path")
    parser.add_argument(
        "--filter", "-f", action="append", help="Filter in format key=value"
    )
    parser.add_argument(
        "--option", "-o", action="append", help="Option in format key=value"
    )
    parser.add_argument(
        "--disabled", action="store_true", help="Create hook in disabled state"
    )

    parsed_args = parser.parse_args(args)

    # Parse filters
    filters = {}
    if parsed_args.filter:
        for f in parsed_args.filter:
            if "=" in f:
                key, value = f.split("=", 1)
                filters[key] = value

    # Parse options
    options = {}
    if parsed_args.option:
        for o in parsed_args.option:
            if "=" in o:
                key, value = o.split("=", 1)
                options[key] = value

    hook = Hook(
        name=parsed_args.name,
        type=HookType(parsed_args.type),
        event=HookEvent(parsed_args.event),
        target=parsed_args.target,
        enabled=not parsed_args.disabled,
        filters=filters,
        options=options,
    )

    registry = HookRegistry()
    if registry.add_hook(hook):
        print(f"Hook '{parsed_args.name}' added successfully.")
    else:
        print(f"Error: Hook with name '{parsed_args.name}' already exists.")


def hook_remove_command(args):
    """Remove a hook."""
    if not args:
        print("Usage: dipeo hook remove <name>")
        return

    name = args[0]
    registry = HookRegistry()

    if registry.remove_hook(name):
        print(f"Hook '{name}' removed successfully.")
    else:
        print(f"Error: Hook '{name}' not found.")


def hook_enable_command(args):
    """Enable a hook."""
    if not args:
        print("Usage: dipeo hook enable <name>")
        return

    name = args[0]
    registry = HookRegistry()

    if registry.enable_hook(name):
        print(f"Hook '{name}' enabled.")
    else:
        print(f"Error: Hook '{name}' not found.")


def hook_disable_command(args):
    """Disable a hook."""
    if not args:
        print("Usage: dipeo hook disable <name>")
        return

    name = args[0]
    registry = HookRegistry()

    if registry.disable_hook(name):
        print(f"Hook '{name}' disabled.")
    else:
        print(f"Error: Hook '{name}' not found.")


async def hook_test_command(args):
    """Test a hook with sample data."""
    if not args:
        print("Usage: dipeo hook test <name>")
        return

    name = args[0]
    registry = HookRegistry()
    hook = registry.get_hook(name)

    if not hook:
        print(f"Error: Hook '{name}' not found.")
        return

    # Create sample event data
    sample_data = {
        "execution_id": "test-execution-123",
        "node_id": "test-node-456",
        "diagram_name": "test-diagram",
        "timestamp": str(asyncio.get_event_loop().time()),
        "output": {"result": "Sample output for testing", "tokens": 100},
    }

    print(f"Testing hook '{name}' with sample data...")
    print(f"Event: {hook.event}")
    print(f"Type: {hook.type}")
    print(f"Target: {hook.target}")

    observer = HookObserver(registry)
    try:
        await observer._execute_hook(hook, sample_data)
        print("Hook executed successfully.")
    except Exception as e:
        print(f"Hook execution failed: {e}")
    finally:
        await observer.cleanup()


def hook_command(args):
    """Main hook command dispatcher."""
    if not args:
        print("Usage: dipeo hook <subcommand> [options]")
        print("\nSubcommands:")
        print("  list              List all hooks")
        print("  add              Add a new hook")
        print("  remove           Remove a hook")
        print("  enable           Enable a hook")
        print("  disable          Disable a hook")
        print("  test             Test a hook with sample data")
        return

    subcommand = args[0]
    subargs = args[1:]

    if subcommand == "list":
        hook_list_command(subargs)
    elif subcommand == "add":
        hook_add_command(subargs)
    elif subcommand == "remove":
        hook_remove_command(subargs)
    elif subcommand == "enable":
        hook_enable_command(subargs)
    elif subcommand == "disable":
        hook_disable_command(subargs)
    elif subcommand == "test":
        import asyncio

        asyncio.run(hook_test_command(subargs))
    else:
        print(f"Unknown subcommand: {subcommand}")
        print("Run 'dipeo hook' for usage information.")


# Add missing import
import os
