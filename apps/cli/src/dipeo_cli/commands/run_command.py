"""Run command for executing diagrams."""

import json
import time
import webbrowser
from pathlib import Path
from typing import Any

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
    ) -> bool:
        """Run a diagram via server."""
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
        try:
            result = self.server.execute_diagram(
                diagram_id=diagram_path,  # Pass file path as diagram_id
                input_variables=input_variables,
                use_unified_monitoring=use_unified,
                diagram_name=diagram_name or Path(diagram_path).stem,
                diagram_format=diagram_format,
            )

            if not result["success"]:
                print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False

            execution_id = result["execution_id"]
            print(f"✓ Execution started: {execution_id}")

            # Open browser if requested (without sensitive data in URL)
            if not no_browser:
                self._open_browser()

            # Poll for completion
            return self._wait_for_completion(execution_id, timeout, debug)

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            return False

    def _open_browser(self):
        """Open browser in monitor mode."""
        monitor_url = "http://localhost:3000/?monitor=true"
        print(f"🌐 Opening browser in monitor mode: {monitor_url}")
        print("📡 Browser will automatically detect CLI execution")
        try:
            # Open in same browser window (new=0)
            if not webbrowser.open(monitor_url, new=0):
                print(
                    "⚠️  Could not open browser automatically. Please open manually:"
                )
                print(f"   {monitor_url}")
        except Exception as e:
            print(f"⚠️  Error opening browser: {e}")
            print(f"   Please open manually: {monitor_url}")

    def _wait_for_completion(self, execution_id: str, timeout: int, debug: bool) -> bool:
        """Poll for execution completion."""
        print(f"\n⏳ Waiting for execution to complete (timeout: {timeout}s)...")
        start_time = time.time()

        try:
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print(f"⏰ Execution timed out after {timeout} seconds")
                    # Stop the server before returning
                    self.server.stop()
                    return False

                time.sleep(2)
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
                        print(
                            f"❌ Execution failed: {exec_result.get('error', 'Unknown error')}"
                        )
                    return False
                if status in ["RUNNING", "PENDING"]:
                    print(f"⏳ Execution {status.lower()}... ({int(elapsed)}s)")
                else:
                    print(f"⏳ Status: {status} ({int(elapsed)}s)")

            return True
        finally:
            # Unregister CLI session before stopping server
            if execution_id:
                self.server.unregister_cli_session(execution_id)

            # Always stop server after execution completes
            self.server.stop()
