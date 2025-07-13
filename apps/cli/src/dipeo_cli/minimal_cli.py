#!/usr/bin/env python3
"""
Minimal DiPeO CLI - Server-only execution (Phase 1 Implementation)

This implementation follows the refactoring plan:
- ~200 lines of code
- Server-based execution only (no local mode)
- Simple HTTP requests for GraphQL (no complex clients)
- Minimal dependencies
"""

import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import yaml

from dipeo.core.constants import BASE_DIR, FILES_DIR


class ServerManager:
    """Manages the backend server process."""

    def __init__(self, port: int = 8000):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
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
        env = {**subprocess.os.environ, "LOG_LEVEL": "DEBUG" if debug else "INFO"}

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

    def execute_diagram(self, diagram_data: Dict[str, Any]) -> Dict[str, Any]:
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

    def get_execution_result(self, execution_id: str) -> Dict[str, Any]:
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


class DiPeOCLI:
    """Minimal DiPeO CLI - thin orchestration layer."""

    def __init__(self):
        self.server = ServerManager()

    def resolve_diagram_path(
        self, diagram: str, format_type: Optional[str] = None
    ) -> str:
        """Resolve diagram path based on format type."""
        # If it looks like a full path (contains / or .), use as-is
        if "/" in diagram or diagram.endswith((".json", ".yaml", ".yml")):
            return diagram

        # Otherwise, construct path based on format
        if not format_type:
            # Try to find the diagram in any format
            for fmt, ext in [
                ("native", ".json"),
                ("light", ".yaml"),
                ("readable", ".yaml"),
            ]:
                path = FILES_DIR / "diagrams" / fmt / f"{diagram}{ext}"
                if path.exists():
                    return str(path)
            raise FileNotFoundError(f"Diagram '{diagram}' not found in any format")

        # Use specified format
        format_map = {
            "light": ("light", ".yaml"),
            "native": ("native", ".json"),
            "readable": ("readable", ".yaml"),
        }

        fmt_dir, ext = format_map[format_type]
        return str(FILES_DIR / "diagrams" / fmt_dir / f"{diagram}{ext}")

    def load_diagram(self, file_path: str) -> Dict[str, Any]:
        """Load diagram from file (JSON or YAML)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        with open(file_path, "r") as f:
            content = f.read()

        # Parse based on extension
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(content)
        else:
            return json.loads(content)

    def run(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: Optional[str] = None,
    ):
        """Run a diagram via server."""
        # Resolve diagram path
        diagram_path = self.resolve_diagram_path(diagram, format_type)
        print(f"📄 Loading diagram: {diagram_path}")

        # Load diagram
        diagram_data = self.load_diagram(diagram_path)

        # Ensure server is running
        if not self.server.start(debug):
            print("❌ Failed to start server")
            return False

        # Execute diagram
        print("🔄 Executing diagram...")
        try:
            result = self.server.execute_diagram(diagram_data)

            if not result["success"]:
                print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False

            execution_id = result["execution_id"]
            print(f"✓ Execution started: {execution_id}")

            # Open browser if requested
            if not no_browser:
                diagram_name = Path(diagram_path).stem
                monitor_url = f"http://localhost:3000/?diagram={diagram_name}&executionId={execution_id}"
                print(f"🌐 Opening browser: {monitor_url}")
                webbrowser.open(monitor_url)

            # Poll for completion
            print(f"\n⏳ Waiting for execution to complete (timeout: {timeout}s)...")
            start_time = time.time()

            try:
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        print(f"⏰ Execution timed out after {timeout} seconds")
                        return False

                    time.sleep(2)
                    exec_result = self.server.get_execution_result(execution_id)

                    if exec_result is None:
                        print(f"⏳ Execution in progress... ({int(elapsed)}s)")
                        continue

                    status = exec_result.get("status")
                    if status == "COMPLETED":
                        print("✅ Execution completed successfully!")
                        break
                    elif status == "FAILED":
                        print(
                            f"❌ Execution failed: {exec_result.get('error', 'Unknown error')}"
                        )
                        return False
                    elif status is None:
                        print(f"⏳ Waiting for execution to start... ({int(elapsed)}s)")
                    else:
                        print(f"⏳ Status: {status} ({int(elapsed)}s)")

                return True
            finally:
                # Always stop server after execution when in debug mode
                if debug:
                    self.server.stop()

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False

    def convert(self, input_path: str, output_path: str):
        """Convert between JSON and YAML formats."""
        print(f"📝 Converting: {input_path} → {output_path}")

        # Load input
        data = self.load_diagram(input_path)

        # Ensure parent directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save in target format
        output_ext = Path(output_path).suffix.lower()

        with open(output_path, "w") as f:
            if output_ext in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(data, f, indent=2)

        print("✓ Conversion complete")

    def stats(self, diagram_path: str):
        """Show diagram statistics."""
        diagram = self.load_diagram(diagram_path)

        # Calculate stats
        nodes = diagram.get("nodes", [])
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        print("\n📊 Diagram Statistics:")
        print(f"  Persons: {len(diagram.get('persons', []))}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Arrows: {len(diagram.get('arrows', []))}")

        if node_types:
            print("\nNode Types:")
            for node_type, count in sorted(node_types.items()):
                print(f"  {node_type}: {count}")

    def monitor(self, diagram_name: Optional[str] = None):
        """Open browser monitor."""
        url = "http://localhost:3000/"
        if diagram_name:
            url += f"?diagram={diagram_name}"
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="DiPeO CLI - Simplified Interface")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a diagram")
    run_parser.add_argument(
        "diagram",
        help="Path to diagram file or diagram name (when using format options)",
    )
    run_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    run_parser.add_argument(
        "--no-browser", action="store_true", help="Skip browser opening"
    )
    run_parser.add_argument("--quiet", action="store_true", help="Minimal output")
    run_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Execution timeout in seconds (default: 300)",
    )

    # Format options (mutually exclusive)
    format_group = run_parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--light", action="store_true", help="Use light format (YAML)"
    )
    format_group.add_argument(
        "--native", action="store_true", help="Use native format (JSON)"
    )
    format_group.add_argument(
        "--readable", action="store_true", help="Use readable format (YAML)"
    )

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show diagram statistics")
    stats_parser.add_argument("diagram", help="Path to diagram file")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Open browser monitor")
    monitor_parser.add_argument("diagram", nargs="?", help="Diagram name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = DiPeOCLI()

    try:
        if args.command == "run":
            # Determine format type
            format_type = None
            if args.light:
                format_type = "light"
            elif args.native:
                format_type = "native"
            elif args.readable:
                format_type = "readable"

            success = cli.run(
                args.diagram, args.debug, args.no_browser, args.timeout, format_type
            )
            sys.exit(0 if success else 1)
        elif args.command == "convert":
            cli.convert(args.input, args.output)
        elif args.command == "stats":
            cli.stats(args.diagram)
        elif args.command == "monitor":
            cli.monitor(args.diagram)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        cli.server.stop()


if __name__ == "__main__":
    main()
