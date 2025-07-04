from typing import Any, TYPE_CHECKING, Optional
from pathlib import Path

from ..execution_options import ExecutionOptions
from ..local_context import LocalAppContext
from ..hooks import HookRegistry, HookObserver

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class LocalDiagramRunner:
    """Handles diagram execution locally without server"""

    def __init__(self, options: ExecutionOptions):
        self.options = options

    async def execute(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Execute diagram locally"""
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None,
        }

        try:
            # Initialize local context
            context = LocalAppContext()
            await context.initialize_for_local()

            # Generate execution ID
            import uuid

            execution_id = str(uuid.uuid4())
            result["execution_id"] = execution_id  # type: ignore

            print(f"🚀 Starting local execution with ID: {execution_id}")

            # Check if hooks are enabled
            custom_observers = []
            hooks_dir = Path("files/hooks")
            if hooks_dir.exists() and (hooks_dir / "hooks.json").exists():
                hook_registry = HookRegistry(hooks_dir)
                if hook_registry.hooks:  # Only add observer if there are hooks
                    hook_observer = HookObserver(hook_registry)
                    custom_observers.append(hook_observer)
                    if self.options.debug:
                        print(f"🪝 Loaded {len(hook_registry.hooks)} hooks")

            # Execute diagram using local execution service
            updates: AsyncIterator[dict[str, Any]] = context.execution_service.execute_diagram(  # type: ignore
                diagram=diagram,
                options={"variables": {}},
                execution_id=execution_id,
                custom_observers=custom_observers,
            )
            async for update in updates:
                # Handle updates
                if update.get("type") == "node_update":
                    node_id = update.get("node_id")
                    status = update.get("status")

                    if status == "running":
                        print(f"\n🔄 Executing node: {node_id}")
                    elif status == "completed":
                        print(f"✅ Node {node_id} completed")
                        if output := update.get("output"):
                            if isinstance(output, dict) and "tokens_used" in output:
                                result["total_token_count"] += output.get(
                                    "tokens_used", 0
                                )  # type: ignore
                elif update.get("type") == "execution_complete":
                    print("\n✨ Execution completed successfully!")
                elif update.get("type") == "execution_error":
                    result["error"] = update.get("error")
                    print(f"\n❌ Execution failed: {update.get('error')}")

        except Exception as e:
            result["error"] = str(e)  # type: ignore
            print(f"\n❌ Error during local execution: {e!s}")
        finally:
            # Cleanup hook observer if used
            if custom_observers:
                for observer in custom_observers:
                    if isinstance(observer, HookObserver):
                        await observer.cleanup()

        return result
