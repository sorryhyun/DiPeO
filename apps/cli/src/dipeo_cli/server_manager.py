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
        except:
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
            "DIPEO_BASE_DIR": str(BASE_DIR)  # Ensure server uses correct base directory
        }

        self.process = subprocess.Popen(
            ["python", "main.py"],
            cwd=server_path,
            env=env,
            stdout=subprocess.PIPE if not debug else None,
            stderr=subprocess.PIPE if not debug else None,
        )

        # Wait for server to be ready
        for i in range(20):  # 10 seconds timeout
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
            self.process.terminate()
            self.process.wait()
            self.process = None

    def execute_diagram(self, diagram_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a diagram via GraphQL."""
        query = """
        mutation ExecuteDiagram($diagramData: JSONScalar) {
            execute_diagram(data: { diagram_data: $diagramData }) {
                success
                execution_id
                error
            }
        }
        """

        response = requests.post(
            f"{self.base_url}/graphql",
            json={"query": query, "variables": {"diagramData": diagram_data}},
        )

        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code}")

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result["data"]["execute_diagram"]

    def get_execution_result(self, execution_id: str) -> dict[str, Any]:
        """Get execution result by ID."""
        query = """
        query GetExecutionResult($id: ExecutionID!) {
            execution(id: $id) {
                status
                node_outputs
                error
            }
        }
        """

        response = requests.post(
            f"{self.base_url}/graphql",
            json={"query": query, "variables": {"id": execution_id}},
        )

        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code}")

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        if "data" not in result or result["data"] is None:
            return None

        return result["data"].get("execution")