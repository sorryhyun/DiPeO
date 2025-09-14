"""Server management for DiPeO CLI."""

import contextlib
import subprocess
import sys
import time
from typing import Any

import requests

from dipeo.config import BASE_DIR
from dipeo.diagram_generated.graphql.inputs import (
    ExecuteDiagramInput,
    RegisterCliSessionInput,
    UnregisterCliSessionInput,
)
from dipeo.diagram_generated.graphql.operations import (
    ExecuteDiagramOperation,
    GetExecutionMetricsOperation,
    GetExecutionOperation,
    RegisterCliSessionOperation,
    UnregisterCliSessionOperation,
)


class ServerManager:
    """Manages the backend server process."""

    def __init__(self, port: int = 8000):
        self.port = port
        self.process: subprocess.Popen | None = None
        self.base_url = f"http://localhost:{port}"

    def is_running(self) -> bool:
        """Check if server is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=1)
            return response.status_code == 200
        except Exception:
            return False

    def start(self, debug: bool = False) -> bool:
        """Start the backend server if not running."""
        if self.is_running():
            print("✓ Server already running")
            return True

        print("🚀 Starting backend server...")

        # Find server directory
        server_path = BASE_DIR / "apps" / "server"
        if not server_path.exists():
            print(f"❌ Server directory not found: {server_path}")
            return False

        # Start server process
        env = {
            **subprocess.os.environ,
            "LOG_LEVEL": "DEBUG" if debug else "INFO",
            "DIPEO_BASE_DIR": str(BASE_DIR),  # Ensure server uses correct base directory
            # Ensure PYTHONPATH includes the project root for module imports
            "PYTHONPATH": str(BASE_DIR)
            + (
                ";" + subprocess.os.environ.get("PYTHONPATH", "")
                if sys.platform == "win32" and subprocess.os.environ.get("PYTHONPATH")
                else ":" + subprocess.os.environ.get("PYTHONPATH", "")
                if subprocess.os.environ.get("PYTHONPATH")
                else ""
            ),
        }

        # On Windows, ensure virtual environment paths are preserved
        if sys.platform == "win32":
            # Preserve VIRTUAL_ENV if it exists
            if "VIRTUAL_ENV" in subprocess.os.environ:
                env["VIRTUAL_ENV"] = subprocess.os.environ["VIRTUAL_ENV"]
            # Preserve PATH to include venv Scripts directory
            if "PATH" in subprocess.os.environ:
                env["PATH"] = subprocess.os.environ["PATH"]

        self.process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=server_path,
            env=env,
            stdout=None,  # Inherit parent's stdout to allow redirection
            stderr=None,  # Inherit parent's stderr to allow redirection
        )

        # Wait for server to be ready
        for _ in range(20):  # 10 seconds timeout
            time.sleep(0.2)
            if self.is_running():
                print("✓ Server started successfully")
                return True

        print("❌ Server failed to start")
        return False

    def stop(self):
        """Stop the server if we started it."""
        if self.process:
            print("🛑 Stopping server...")
            process = self.process
            self.process = None  # Mark as stopped immediately to prevent double-stop

            # First try terminate
            process.terminate()
            try:
                # Wait up to 2 seconds for graceful shutdown
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                print("⚠️  Server didn't stop gracefully, forcing shutdown...")
                process.kill()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # If even kill doesn't work, use OS-level kill
                    import os as os_module
                    import signal

                    with contextlib.suppress(ProcessLookupError):
                        os_module.kill(process.pid, signal.SIGKILL)

    def execute_diagram(
        self,
        diagram_data: dict[str, Any] | None = None,
        diagram_id: str | None = None,
        input_variables: dict[str, Any] | None = None,
        use_unified_monitoring: bool = False,
        diagram_name: str | None = None,
        diagram_format: str | None = None,
    ) -> dict[str, Any]:
        """Execute a diagram via GraphQL."""
        # Create Strawberry input object for better type safety
        execute_input = ExecuteDiagramInput(
            diagram_id=diagram_id,
            diagram_data=diagram_data,
            variables=input_variables,
        )

        # Use operation class to get query and build variables (now with Strawberry object)
        variables = ExecuteDiagramOperation.get_variables_dict(input=execute_input)

        response = requests.post(
            f"{self.base_url}/graphql",
            json={
                "query": ExecuteDiagramOperation.get_query(),
                "variables": variables,
            },
        )

        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code}")

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        execution_result = result["data"]["execute_diagram"]

        # Register CLI session if execution started successfully
        if execution_result.get("success") and execution_result.get("execution"):
            execution_id = execution_result["execution"]["id"]

            self.register_cli_session(
                execution_id=execution_id,
                diagram_name=diagram_name or "unknown",
                diagram_format=diagram_format or "native",
                diagram_data=diagram_data,  # Send diagram data for faster loading
            )

        return execution_result

    def get_execution_result(self, execution_id: str) -> dict[str, Any] | None:
        """Get execution result by ID."""
        # Use operation class to get query and build variables
        variables = GetExecutionOperation.get_variables_dict(execution_id=execution_id)

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": GetExecutionOperation.get_query(), "variables": variables},
                timeout=5,
            )

            if response.status_code != 200:
                print(f"[DEBUG] GraphQL request failed: {response.status_code}")
                print(f"[DEBUG] Response body: {response.text}")
                return None

            result = response.json()

            if "errors" in result:
                print(
                    f"[ERROR] GraphQL errors while fetching execution {execution_id}: {result['errors']}"
                )
                return None

            if "data" not in result or result["data"] is None:
                return None

            return result["data"].get("get_execution")
        except Exception as e:
            print(f"[DEBUG] Error getting execution result: {e}")
            import traceback

            traceback.print_exc()
            return None

    def get_execution_metrics(self, execution_id: str) -> dict[str, Any] | None:
        """Get execution metrics by ID."""
        # Use operation class to get query and build variables
        variables = GetExecutionMetricsOperation.get_variables_dict(execution_id=execution_id)

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": GetExecutionMetricsOperation.get_query(), "variables": variables},
                timeout=5,
            )

            if response.status_code != 200:
                return None

            result = response.json()

            if "errors" in result or "data" not in result:
                return None

            return result["data"].get("get_execution_metrics")
        except Exception:
            return None

    def register_cli_session(
        self,
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: dict[str, Any] | None = None,
        diagram_path: str | None = None,
    ) -> bool:
        """Register a CLI execution session with the server."""
        # Convert lowercase format to uppercase for GraphQL enum
        diagram_format_upper = diagram_format.upper()

        # Create Strawberry input object for better type safety
        register_input = RegisterCliSessionInput(
            execution_id=execution_id,
            diagram_name=diagram_name,
            diagram_format=diagram_format_upper,
            diagram_data=diagram_data,
        )

        # Use operation class to get query and build variables (now with Strawberry object)
        variables = RegisterCliSessionOperation.get_variables_dict(input=register_input)

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={
                    "query": RegisterCliSessionOperation.get_query(),
                    "variables": variables,
                },
                timeout=5,
            )

            if response.status_code == 200:
                result = response.json()
                if "data" in result and result["data"]["register_cli_session"]["success"]:
                    print("📡 CLI session registered for monitoring")
                    return True
        except Exception as e:
            print(f"[DEBUG] Failed to register CLI session: {e}")

        return False

    def unregister_cli_session(self, execution_id: str) -> bool:
        """Unregister a CLI execution session."""
        # Create Strawberry input object for better type safety
        unregister_input = UnregisterCliSessionInput(execution_id=execution_id)

        # Use operation class to get query and build variables (now with Strawberry object)
        variables = UnregisterCliSessionOperation.get_variables_dict(input=unregister_input)

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": UnregisterCliSessionOperation.get_query(), "variables": variables},
                timeout=5,
            )

            if response.status_code == 200:
                return True
        except Exception:
            pass

        return False
