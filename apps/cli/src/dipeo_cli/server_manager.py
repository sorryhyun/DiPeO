"""Server management for DiPeO CLI."""

import subprocess
import time
from typing import Any

import requests
from dipeo.core.constants import BASE_DIR


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
            "DIPEO_BASE_DIR": str(
                BASE_DIR
            ),  # Ensure server uses correct base directory
        }

        self.process = subprocess.Popen(
            ["python", "main.py"],
            cwd=server_path,
            env=env,
            stdout=None,  # Inherit parent's stdout to allow redirection
            stderr=None,  # Inherit parent's stderr to allow redirection
        )

        # Wait for server to be ready
        for _ in range(20):  # 10 seconds timeout
            time.sleep(0.5)
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
            
            process.terminate()
            try:
                # Wait up to 5 seconds for graceful shutdown
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                print("⚠️  Server didn't stop gracefully, forcing shutdown...")
                process.kill()
                process.wait()

    def execute_diagram(
        self,
        diagram_data: dict[str, Any],
        input_variables: dict[str, Any] | None = None,
        use_unified_monitoring: bool = False,
        diagram_name: str | None = None,
        diagram_format: str | None = None,
    ) -> dict[str, Any]:
        """Execute a diagram via GraphQL."""
        query = """
        mutation ExecuteDiagram($diagramData: JSON, $variables: JSON, $useUnifiedMonitoring: Boolean) {
            execute_diagram(input: {
                diagram_data: $diagramData,
                variables: $variables,
                use_unified_monitoring: $useUnifiedMonitoring
            }) {
                success
                execution_id
                error
            }
        }
        """

        response = requests.post(
            f"{self.base_url}/graphql",
            json={
                "query": query,
                "variables": {
                    "diagramData": diagram_data,
                    "variables": input_variables,
                    "useUnifiedMonitoring": use_unified_monitoring,
                },
            },
        )

        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code}")

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        execution_result = result["data"]["execute_diagram"]

        # Register CLI session if execution started successfully
        if execution_result.get("success") and execution_result.get("execution_id"):
            self.register_cli_session(
                execution_id=execution_result["execution_id"],
                diagram_name=diagram_name or "unknown",
                diagram_format=diagram_format or "native",
                diagram_data=diagram_data,
            )

        return execution_result

    def get_execution_result(self, execution_id: str) -> dict[str, Any] | None:
        """Get execution result by ID."""
        query = """
        query GetExecutionResult($id: ID!) {
            execution(id: $id) {
                status
                node_outputs
                error
            }
        }
        """

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": query, "variables": {"id": execution_id}},
                timeout=5,
            )

            if response.status_code != 200:
                print(f"[DEBUG] GraphQL request failed: {response.status_code}")
                print(f"[DEBUG] Response body: {response.text}")
                return None

            result = response.json()

            if "errors" in result:
                print(f"[ERROR] GraphQL errors: {result['errors']}")
                return None

            if "data" not in result or result["data"] is None:
                return None

            return result["data"].get("execution")
        except Exception as e:
            print(f"[DEBUG] Error getting execution result: {e}")
            import traceback

            traceback.print_exc()
            return None

    def register_cli_session(
        self,
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: dict[str, Any] | None = None,
    ) -> bool:
        """Register a CLI execution session with the server."""
        mutation = """
        mutation RegisterCliSession($executionId: String!, $diagramName: String!, $diagramFormat: String!, $diagramData: JSON) {
            register_cli_session(input: {
                execution_id: $executionId,
                diagram_name: $diagramName,
                diagram_format: $diagramFormat,
                diagram_data: $diagramData
            }) {
                success
                error
            }
        }
        """

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={
                    "query": mutation,
                    "variables": {
                        "executionId": execution_id,
                        "diagramName": diagram_name,
                        "diagramFormat": diagram_format,
                        "diagramData": diagram_data,
                    },
                },
                timeout=5,
            )

            if response.status_code == 200:
                result = response.json()
                if (
                    "data" in result
                    and result["data"]["register_cli_session"]["success"]
                ):
                    print("📡 CLI session registered for monitoring")
                    return True
        except Exception as e:
            print(f"[DEBUG] Failed to register CLI session: {e}")

        return False

    def unregister_cli_session(self, execution_id: str) -> bool:
        """Unregister a CLI execution session."""
        mutation = """
        mutation UnregisterCliSession($executionId: String!) {
            unregister_cli_session(input: { execution_id: $executionId }) {
                success
            }
        }
        """

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": mutation, "variables": {"executionId": execution_id}},
                timeout=5,
            )

            if response.status_code == 200:
                return True
        except Exception:
            pass

        return False
