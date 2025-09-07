"""Ask command for natural language diagram generation and execution."""

import json
import time
from pathlib import Path

from ..server_manager import ServerManager
from .base import DiagramLoader


class AskCommand:
    """Command for generating and optionally running diagrams from natural language."""

    # Path to the diagram generator
    GENERATOR_DIAGRAM = "projects/dipeodipeo/test"
    GENERATED_DIAGRAM_PATH = "projects/dipeodipeo/generated/diagram.light.yaml"

    def __init__(self, server: ServerManager):
        self.server = server
        self.loader = DiagramLoader()

    def execute(
        self,
        request: str,
        and_run: bool = False,
        debug: bool = False,
        timeout: int = 90,
        run_timeout: int = 300,
        no_browser: bool = True,
    ) -> bool:
        """
        Generate a diagram from natural language and optionally run it.

        Args:
            request: Natural language description of what to create
            and_run: Whether to run the generated diagram after creation
            debug: Enable debug output
            timeout: Timeout for generation (default 90s)
            run_timeout: Timeout for running generated diagram (default 300s)
            no_browser: Don't open browser (default True)

        Returns:
            True if successful, False otherwise
        """
        print(f'🤖 Processing request: "{request}"')

        # Prepare input data for the generator diagram
        input_variables = {
            "user_requirements": request,
            "workflow_description": request,
        }

        # Resolve generator diagram path
        generator_path = self.loader.resolve_diagram_path(
            self.GENERATOR_DIAGRAM, "light"
        )
        print(f"📄 Using generator: {generator_path}")

        # Ensure server is running
        if not self.server.start(debug):
            print("❌ Failed to start server")
            return False

        # Execute the generator diagram
        print("🔄 Generating diagram...")
        if debug:
            print(f"📥 Input: {json.dumps(input_variables, indent=2)}")

        try:
            # Run the generator
            result = self.server.execute_diagram(
                diagram_id=generator_path,
                input_variables=input_variables,
                use_unified_monitoring=True,
                diagram_name="diagram_generator",
                diagram_format="light",
            )

            if not result["success"]:
                print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                return False

            execution_id = result["execution_id"]
            print(f"✓ Generation started: {execution_id}")

            # Wait for generation to complete
            if not self._wait_for_completion(
                execution_id, timeout, debug, "Generation"
            ):
                return False

            print("✅ Diagram generated successfully!")
            print(f"📁 Generated diagram: {self.GENERATED_DIAGRAM_PATH}")

            # If --and-run flag is set, execute the generated diagram
            if and_run:
                return self._run_generated_diagram(debug, run_timeout, no_browser)

            return True

        except Exception as e:
            print(f"❌ Error during generation: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False
        finally:
            # Stop server if not running generated diagram
            if not and_run:
                self.server.stop()

    def _run_generated_diagram(
        self, debug: bool, timeout: int, no_browser: bool
    ) -> bool:
        """Run the generated diagram."""
        print("\n" + "=" * 50)
        print("🚀 Running generated diagram...")
        print("=" * 50 + "\n")

        # Check if generated diagram exists
        generated_path = Path(self.GENERATED_DIAGRAM_PATH)
        if not generated_path.exists():
            print(f"❌ Generated diagram not found: {self.GENERATED_DIAGRAM_PATH}")
            return False

        try:
            # Execute the generated diagram
            result = self.server.execute_diagram(
                diagram_id=str(generated_path),
                input_variables=None,
                use_unified_monitoring=True,
                diagram_name=generated_path.stem,
                diagram_format="light",
            )

            if not result["success"]:
                print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False

            execution_id = result["execution_id"]
            print(f"✓ Execution started: {execution_id}")

            # Open browser if requested
            if not no_browser:
                self._open_browser()

            # Wait for execution to complete
            return self._wait_for_completion(execution_id, timeout, debug, "Execution")

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False
        finally:
            self.server.stop()

    def _open_browser(self):
        """Open browser in monitor mode."""
        import webbrowser

        monitor_url = "http://localhost:3000/?monitor=true"
        print(f"🌐 Opening browser: {monitor_url}")
        try:
            if not webbrowser.open(monitor_url, new=0):
                print(f"⚠️  Could not open browser. Please open manually: {monitor_url}")
        except Exception as e:
            print(f"⚠️  Error opening browser: {e}")

    def _wait_for_completion(
        self, execution_id: str, timeout: int, debug: bool, phase: str
    ) -> bool:
        """Poll for execution completion."""
        print(f"⏳ Waiting for {phase.lower()} to complete (timeout: {timeout}s)...")
        start_time = time.time()

        try:
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print(f"⏰ {phase} timed out after {timeout} seconds")
                    return False

                time.sleep(2)
                exec_result = self.server.get_execution_result(execution_id)

                if exec_result is None:
                    print(f"⏳ Waiting... ({int(elapsed)}s)")
                    continue

                status = exec_result.get("status")

                if status in ["COMPLETED", "MAXITER_REACHED"]:
                    if status == "MAXITER_REACHED":
                        print(f"✅ {phase} completed (max iterations reached)")
                    else:
                        print(f"✅ {phase} completed successfully!")
                    return True

                if status in ["FAILED", "ABORTED"]:
                    error_msg = exec_result.get("error", "Unknown error")
                    if status == "ABORTED":
                        print(f"❌ {phase} aborted")
                    else:
                        print(f"❌ {phase} failed: {error_msg}")
                    return False

                if status in ["RUNNING", "PENDING"]:
                    print(f"⏳ {phase} {status.lower()}... ({int(elapsed)}s)")
                else:
                    print(f"⏳ Status: {status} ({int(elapsed)}s)")

        finally:
            # Unregister CLI session
            if execution_id:
                self.server.unregister_cli_session(execution_id)
