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
        # If it's an absolute path, use as-is
        path = Path(diagram)
        if path.is_absolute():
            return diagram

        # If it has a file extension, check if it exists
        if diagram.endswith((".native.json", ".light.yaml", ".readable.yaml")):
            # Check if it exists as-is
            if Path(diagram).exists():
                return diagram
            # Try with files/ prefix
            path_with_files = FILES_DIR / diagram
            if path_with_files.exists():
                return str(path_with_files)
            # If it starts with files/, also try resolving from project root
            if diagram.startswith("files/"):
                return str(FILES_DIR.parent / diagram)

        # For paths without extension, auto-prepend files/ if not present
        if diagram.startswith("files/"):
            diagram_path = diagram[6:]  # Remove "files/"
        else:
            diagram_path = diagram

        if not format_type:
            # Try to find the diagram with known extensions
            extensions = [".native.json", ".light.yaml", ".readable.yaml"]

            for ext in extensions:
                path = FILES_DIR / f"{diagram_path}{ext}"
                if path.exists():
                    return str(path)

            raise FileNotFoundError(f"Diagram '{diagram}' not found in any format")

        # Use specified format
        format_map = {
            "light": ".light.yaml",
            "native": ".native.json",
            "readable": ".readable.yaml",
        }

        ext = format_map.get(format_type)
        if not ext:
            raise ValueError(f"Unknown format type: {format_type}")

        path = FILES_DIR / f"{diagram_path}{ext}"
        return str(path)

    def load_diagram(self, file_path: str) -> dict[str, Any]:
        """Load diagram from file (JSON or YAML)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        with path.open(encoding="utf-8") as f:
            content = f.read()

        # Parse based on extension
        if str(path).endswith((".light.yaml", ".readable.yaml")):
            return yaml.safe_load(content)
        if str(path).endswith(".native.json"):
            return json.loads(content)
        raise ValueError(f"Unknown diagram file format: {file_path}")

    def run(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
        input_variables: dict[str, Any] | None = None,
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

        # Store diagram path for browser URL
        if not no_browser:
            # Convert absolute path to relative path from files/ directory
            path = Path(diagram_path)
            try:
                # Try to make path relative to FILES_DIR
                from dipeo.core.constants import FILES_DIR

                relative_path = path.relative_to(FILES_DIR)
                # Remove format suffix from the relative path
                path_str = str(relative_path)
                for suffix in [".native.json", ".light.yaml", ".readable.yaml"]:
                    if path_str.endswith(suffix):
                        path_str = path_str[: -len(suffix)]
                        break
                diagram_name = path_str
            except ValueError:
                # If not under FILES_DIR, use the original logic
                name = path.name
                for suffix in [".native.json", ".light.yaml", ".readable.yaml"]:
                    if name.endswith(suffix):
                        name = name[: -len(suffix)]
                        break
                diagram_name = name
        else:
            diagram_name = None

        # Determine diagram format
        diagram_format = "native"  # default
        if diagram_path.endswith(".light.yaml"):
            diagram_format = "light"
        elif diagram_path.endswith(".readable.yaml"):
            diagram_format = "readable"

        # Execute diagram
        print("🔄 Executing diagram...")
        if input_variables:
            print(f"📥 With input variables: {json.dumps(input_variables, indent=2)}")
        try:
            result = self.server.execute_diagram(
                diagram_data,
                input_variables,
                use_monitoring_stream=True,
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
                monitor_url = f"http://localhost:3000/?monitor=true"
                print(f"🌐 Opening browser in monitor mode: {monitor_url}")
                print(f"📡 Browser will automatically detect CLI execution")
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

            # Poll for completion
            print(f"\n⏳ Waiting for execution to complete (timeout: {timeout}s)...")
            start_time = time.time()

            try:
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        print(f"⏰ Execution timed out after {timeout} seconds")
                        # Stop the server before returning
                        print("🛑 Stopping server...")
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
                print("🛑 Stopping server...")
                self.server.stop()

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return False

    def convert(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ):
        """Convert between diagram formats using the integrated diagram service."""
        print(f"📝 Converting: {input_path} → {output_path}")

        # Auto-detect formats from file extensions if not provided
        if not from_format:
            input_name = Path(input_path).name.lower()
            if input_name.endswith(".native.json"):
                from_format = "native"
            elif input_name.endswith(".light.yaml"):
                from_format = "light"
            elif input_name.endswith(".readable.yaml"):
                from_format = "readable"
            else:
                raise ValueError(
                    f"Cannot determine format from input file: {input_path}"
                )

        if not to_format:
            output_name = Path(output_path).name.lower()
            if output_name.endswith(".native.json"):
                to_format = "native"
            elif output_name.endswith(".light.yaml"):
                to_format = "light"
            elif output_name.endswith(".readable.yaml"):
                to_format = "readable"
            else:
                raise ValueError(
                    f"Cannot determine format from output file: {output_path}"
                )

        print(f"  Format: {from_format} → {to_format}")

        # If same format, just copy the file
        if from_format == to_format:
            # Load and save to handle any formatting differences
            data = self.load_diagram(input_path)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with Path(output_path).open("w", encoding="utf-8") as f:
                if output_path.endswith(".json"):
                    json.dump(data, f, indent=2)
                else:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            print("✓ Conversion complete")
            return

        # Use the unified converter for format conversion
        try:
            # Import required modules
            from dipeo.domain.diagram.unified_converter import UnifiedDiagramConverter

            # Create converter
            converter = UnifiedDiagramConverter()

            # Load the diagram data
            with Path(input_path).open(encoding="utf-8") as f:
                content = f.read()

            # Convert: deserialize from source format, serialize to target format
            diagram = converter.deserialize(content, format_id=from_format)
            output_content = converter.serialize(diagram, format_id=to_format)

            # Save the converted content
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with Path(output_path).open("w", encoding="utf-8") as f:
                f.write(output_content)

            print("✓ Conversion complete")

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            raise

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
        webbrowser.open(url, new=0)
