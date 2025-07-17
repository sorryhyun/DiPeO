"""DiPeO CLI - Main orchestration layer."""

import json
import time
import webbrowser
from pathlib import Path
from typing import Any

import yaml

from dipeo.core.constants import FILES_DIR

from .server_manager import ServerManager


class DiPeOCLI:
    """Minimal DiPeO CLI - thin orchestration layer."""

    def __init__(self):
        self.server = ServerManager()

    def resolve_diagram_path(self, diagram: str, format_type: str | None = None) -> str:
        """Resolve diagram path based on format type."""
        # If it's an absolute path or starts with files/, use as-is
        path = Path(diagram)
        if path.is_absolute() or diagram.startswith("files/"):
            return diagram

        # If it has a file extension, check if it exists relative to current dir
        if diagram.endswith(
            (".json", ".yaml", ".yml", ".native.json", ".light.yaml", ".readable.yaml")
        ):
            if Path(diagram).exists():
                return diagram

        # Otherwise, construct path based on format within diagrams directory
        diagrams_dir = FILES_DIR / "diagrams"

        if not format_type:
            # Try to find the diagram with new extensions first
            new_extensions = [
                (".native.json", "native"),
                (".light.yaml", "light"),
                (".readable.yaml", "readable"),
            ]

            # Check new extension format
            for ext, _ in new_extensions:
                path = diagrams_dir / f"{diagram}{ext}"
                if path.exists():
                    return str(path)

            # Fallback to old format (backward compatibility)
            for fmt, ext in [
                ("native", ".json"),
                ("light", ".yaml"),
                ("readable", ".yaml"),
            ]:
                # Handle subdirectories in old format
                if "/" in diagram:
                    parts = diagram.split("/")
                    old_path = (
                        diagrams_dir / fmt / "/".join(parts[:-1]) / f"{parts[-1]}{ext}"
                    )
                else:
                    old_path = diagrams_dir / fmt / f"{diagram}{ext}"
                if old_path.exists():
                    return str(old_path)

            raise FileNotFoundError(f"Diagram '{diagram}' not found in any format")

        # Use specified format
        format_map = {
            "light": ".light.yaml",
            "native": ".native.json",
            "readable": ".readable.yaml",
        }

        # Try new extension format first
        ext = format_map[format_type]
        path = diagrams_dir / f"{diagram}{ext}"
        if path.exists():
            return str(path)

        # Fallback to old format
        old_format_map = {
            "light": ("light", ".yaml"),
            "native": ("native", ".json"),
            "readable": ("readable", ".yaml"),
        }
        fmt_dir, old_ext = old_format_map[format_type]
        # Handle subdirectories in old format
        if "/" in diagram:
            parts = diagram.split("/")
            old_path = (
                diagrams_dir / fmt_dir / "/".join(parts[:-1]) / f"{parts[-1]}{old_ext}"
            )
        else:
            old_path = diagrams_dir / fmt_dir / f"{diagram}{old_ext}"
        if old_path.exists():
            return str(old_path)

        # If neither exists, return the new format path (for creating new files)
        return str(path)

    def load_diagram(self, file_path: str) -> dict[str, Any]:
        """Load diagram from file (JSON or YAML)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        with open(file_path) as f:
            content = f.read()

        # Parse based on extension
        if str(path).endswith((".light.yaml", ".readable.yaml")) or path.suffix in [
            ".yaml",
            ".yml",
        ]:
            return yaml.safe_load(content)
        elif str(path).endswith(".native.json") or path.suffix == ".json":
            return json.loads(content)
        else:
            # Try to parse as YAML first, then JSON
            try:
                return yaml.safe_load(content)
            except:
                return json.loads(content)

    def run(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
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

        # Store diagram name for later use
        diagram_name = Path(diagram_path).stem if not no_browser else None

        # Execute diagram
        print("🔄 Executing diagram...")
        try:
            result = self.server.execute_diagram(diagram_data)

            if not result["success"]:
                print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False

            execution_id = result["execution_id"]
            print(f"✓ Execution started: {execution_id}")

            # Open browser with execution ID if requested (only once)
            if not no_browser:
                monitor_url = f"http://localhost:3000/?diagram={diagram_name}&executionId={execution_id}&monitor=true"
                print(f"🌐 Opening browser in monitor mode: {monitor_url}")
                webbrowser.open(monitor_url)

            # Poll for completion
            print(f"\n⏳ Waiting for execution to complete (timeout: {timeout}s)...")
            start_time = time.time()

            try:
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        print(f"⏰ Execution timed out after {timeout} seconds")
                        # Stop the server before returning
                        if debug:
                            print("🛑 Stopping server...")
                            self.server.stop()
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
                    if status == "FAILED":
                        print(
                            f"❌ Execution failed: {exec_result.get('error', 'Unknown error')}"
                        )
                        return False
                    if status is None:
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

    def monitor(self, diagram_name: str | None = None):
        """Open browser monitor."""
        url = "http://localhost:3000/"
        if diagram_name:
            url += f"?diagram={diagram_name}"
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
