"""Run command for executing diagrams."""

import asyncio
import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any

from dipeo.infrastructure.logging_config import setup_logging

from ..display.execution_display import ExecutionDisplay, SimpleDisplay
from ..display.subscription_client import SimpleSubscriptionClient, SubscriptionClient
from ..server_manager import ServerManager
from .base import DiagramLoader


class RunCommand:
    """Command for running diagrams."""

    def __init__(self, server: ServerManager):
        self.server = server
        self.loader = DiagramLoader()

    def execute(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
        input_variables: dict[str, Any] | None = None,
        use_unified: bool = False,
        simple: bool = False,
    ) -> bool:
        """Run a diagram via server."""
        # Setup logging if debug mode is enabled
        if debug:
            setup_logging(
                component="cli",
                log_level="DEBUG",
                log_to_file=True,
                log_dir=".logs",
                console_output=False,  # Avoid duplicate console output
            )

        # Resolve diagram path
        diagram_path = self.loader.resolve_diagram_path(diagram, format_type)
        print(f"📄 Loading diagram: {diagram_path}")

        # Ensure server is running
        if not self.server.start(debug):
            print("❌ Failed to start server")
            return False

        # Store diagram path for browser URL
        if not no_browser:
            diagram_name = self.loader.get_diagram_name(diagram_path)
        else:
            diagram_name = None

        # Determine diagram format
        diagram_format = self.loader.get_diagram_format(diagram_path)

        # Execute diagram
        print("🔄 Executing diagram...")
        if input_variables:
            print(f"📥 With input variables: {json.dumps(input_variables, indent=2)}")

        execution_id = None
        try:
            result = self.server.execute_diagram(
                diagram_id=diagram_path,  # Pass file path as diagram_id
                input_variables=input_variables,
                use_unified_monitoring=use_unified,
                diagram_name=diagram_name or diagram_path,  # Pass full path for backend to load
                diagram_format=diagram_format,
            )

            if not result["success"]:
                print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False

            # Get execution ID from nested structure
            if not result.get("execution") or not result["execution"].get("id"):
                print("❌ No execution ID returned")
                return False
            execution_id = result["execution"]["id"]

            # Use simple display mode if requested or if subscriptions fail
            if simple:
                print(f"✓ Execution started: {execution_id}")
                return self._wait_for_completion_simple(execution_id, timeout, debug)
            else:
                # Try to use rich display with subscriptions
                return self._wait_for_completion_rich(
                    execution_id, diagram_name or Path(diagram_path).stem, timeout, debug
                )

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False
        finally:
            # Always stop server when execute() exits, regardless of outcome
            # Unregister CLI session if we have an execution_id
            if execution_id:
                with contextlib.suppress(Exception):
                    self.server.unregister_cli_session(execution_id)

            # Stop the server
            self.server.stop()

            # Small delay to ensure server cleanup completes
            time.sleep(0.1)

    def _wait_for_completion_simple(self, execution_id: str, timeout: int, debug: bool) -> bool:
        """Poll for execution completion in simple mode."""
        print(f"\n⏳ Waiting for execution to complete (timeout: {timeout}s)...")
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print(f"⏰ Execution timed out after {timeout} seconds")
                # Stop the server before returning
                self.server.stop()
                return False

            time.sleep(2)  # Reduced polling interval for faster response
            exec_result = self.server.get_execution_result(execution_id)

            if exec_result is None:
                print(f"⏳ Waiting for execution result... ({int(elapsed)}s)")
                continue

            status = exec_result.get("status")

            if status in ["COMPLETED", "MAXITER_REACHED"]:
                if status == "MAXITER_REACHED":
                    print("✅ Execution completed (max iterations reached)")
                else:
                    print("✅ Execution completed successfully!")
                break
            if status in ["FAILED", "ABORTED"]:
                if status == "ABORTED":
                    print("❌ Execution aborted")
                else:
                    print(f"❌ Execution failed: {exec_result.get('error', 'Unknown error')}")
                return False
            if status in ["RUNNING", "PENDING"]:
                print(f"⏳ Execution {status.lower()}... ({int(elapsed)}s)")
            else:
                print(f"⏳ Status: {status} ({int(elapsed)}s)")

        return True

    def _wait_for_completion_rich(
        self, execution_id: str, diagram_name: str, timeout: int, debug: bool
    ) -> bool:
        """Wait for execution completion with rich display."""
        try:
            # Create display
            display = ExecutionDisplay(diagram_name, execution_id, debug)
            display.start()

            # Try WebSocket client first, fallback to polling if it fails
            try:
                # Use WebSocket subscription client for real-time updates
                ws_url = f"http://localhost:{self.server.port}"
                client = SubscriptionClient(ws_url, execution_id)
            except Exception:
                # Fallback to polling client
                client = SimpleSubscriptionClient(self.server, execution_id)

            # Get initial state
            exec_result = self.server.get_execution_result(execution_id)
            if exec_result:
                display.update_from_state(exec_result)

            # Run async subscription with a clean loop (ensures full teardown)
            async def run_subscription():
                await client.connect()
                try:
                    subscription_task = asyncio.create_task(
                        client.subscribe_to_execution(display.handle_event)
                    )
                    start = time.time()
                    while True:
                        # Check timeout
                        if time.time() - start > timeout:
                            print(f"\n⏰ Execution timed out after {timeout} seconds")
                            subscription_task.cancel()
                            return False

                        # Check execution status
                        exec_result = self.server.get_execution_result(execution_id)
                        if exec_result:
                            status = exec_result.get("status")
                            if status in ["COMPLETED", "MAXITER_REACHED"]:
                                if status == "MAXITER_REACHED":
                                    print("\n✅ Execution completed (max iterations reached)")
                                else:
                                    print("\n✅ Execution completed successfully!")
                                subscription_task.cancel()
                                return True
                            elif status in ["FAILED", "ABORTED"]:
                                if status == "ABORTED":
                                    print("\n❌ Execution aborted")
                                else:
                                    print(
                                        f"\n❌ Execution failed: {exec_result.get('error', 'Unknown error')}"
                                    )
                                subscription_task.cancel()
                                return False

                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    raise
                finally:
                    await client.disconnect()

            try:
                return asyncio.run(run_subscription())
            except KeyboardInterrupt:
                raise
            finally:
                display.stop()

        except KeyboardInterrupt:
            # Re-raise keyboard interrupt
            raise
        except Exception as e:
            if debug:
                print(f"Rich display failed: {e}")
                import traceback

                traceback.print_exc()

            # Fallback to simple mode
            print("Falling back to simple display mode...")
            return self._wait_for_completion_simple(execution_id, timeout, debug)
