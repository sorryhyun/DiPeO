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
        use_unified: bool = False,
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
    
    def metrics(
        self,
        execution_id: str | None = None,
        diagram_id: str | None = None,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ):
        """Display execution metrics."""
        import requests
        from datetime import datetime
        
        # Ensure server is running
        if not self.server.ensure_running():
            print("❌ Failed to start server")
            return
        
        try:
            # GraphQL endpoint
            url = "http://localhost:8000/graphql"
            
            if execution_id:
                # Query specific execution metrics
                query = """
                query ExecutionMetrics($executionId: ID!) {
                    execution(id: $executionId) {
                        id
                        status
                        diagramId
                        startedAt
                        endedAt
                        durationSeconds
                        metrics
                    }
                }
                """
                variables = {"executionId": execution_id}
                
                response = requests.post(
                    url,
                    json={"query": query, "variables": variables},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    print(f"❌ GraphQL errors: {result['errors']}")
                    return
                
                execution = result.get("data", {}).get("execution")
                if not execution:
                    print(f"❌ Execution {execution_id} not found")
                    return
                
                metrics = execution.get("metrics")
                if not metrics:
                    print(f"⚠️ No metrics available for execution {execution_id}")
                    return
                
                if output_json:
                    print(json.dumps(metrics, indent=2))
                else:
                    self._display_metrics(execution, metrics, bottlenecks_only, optimizations_only)
                    
            elif diagram_id:
                # Query execution history for diagram
                query = """
                query ExecutionHistory($diagramId: ID!, $includeMetrics: Boolean!) {
                    executionHistory(diagramId: $diagramId, limit: 10, includeMetrics: $includeMetrics) {
                        id
                        status
                        startedAt
                        endedAt
                        durationSeconds
                        metrics
                    }
                }
                """
                variables = {
                    "diagramId": diagram_id,
                    "includeMetrics": True
                }
                
                response = requests.post(
                    url,
                    json={"query": query, "variables": variables},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    print(f"❌ GraphQL errors: {result['errors']}")
                    return
                
                executions = result.get("data", {}).get("executionHistory", [])
                if not executions:
                    print(f"⚠️ No executions found for diagram {diagram_id}")
                    return
                
                if output_json:
                    print(json.dumps(executions, indent=2))
                else:
                    self._display_history_metrics(executions, bottlenecks_only, optimizations_only)
                    
            else:
                # Show latest execution
                query = """
                query LatestExecution {
                    executions(limit: 1) {
                        id
                        status
                        diagramId
                        startedAt
                        endedAt
                        durationSeconds
                        metrics
                    }
                }
                """
                
                response = requests.post(
                    url,
                    json={"query": query},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    print(f"❌ GraphQL errors: {result['errors']}")
                    return
                
                executions = result.get("data", {}).get("executions", [])
                if not executions:
                    print("⚠️ No executions found")
                    return
                
                execution = executions[0]
                metrics = execution.get("metrics")
                
                if not metrics:
                    print(f"⚠️ No metrics available for latest execution")
                    return
                
                if output_json:
                    print(json.dumps(metrics, indent=2))
                else:
                    self._display_metrics(execution, metrics, bottlenecks_only, optimizations_only)
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch metrics: {e}")
        except Exception as e:
            print(f"❌ Error displaying metrics: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_metrics(self, execution, metrics, bottlenecks_only, optimizations_only):
        """Display formatted metrics for a single execution."""
        print("\n📊 Execution Metrics")
        print("=" * 60)
        print(f"Execution ID: {execution['id']}")
        print(f"Diagram ID: {execution.get('diagramId', 'N/A')}")
        print(f"Status: {execution['status']}")
        print(f"Duration: {execution.get('durationSeconds', 0):.2f}s")
        
        if not bottlenecks_only and not optimizations_only:
            # Show general metrics
            print(f"\n⏱️ Performance Summary:")
            print(f"  Total Duration: {metrics.get('total_duration_ms', 0):.0f}ms")
            print(f"  Node Count: {len(metrics.get('node_metrics', {}))}")
            
            # Show critical path
            critical_path = metrics.get('critical_path', [])
            if critical_path:
                print(f"\n🛤️ Critical Path ({len(critical_path)} nodes):")
                for node_id in critical_path[:5]:  # Show top 5
                    node_metric = metrics.get('node_metrics', {}).get(node_id, {})
                    duration = node_metric.get('duration_ms', 0)
                    node_type = node_metric.get('node_type', 'unknown')
                    print(f"  • {node_id} ({node_type}): {duration:.0f}ms")
        
        # Show bottlenecks
        if not optimizations_only:
            bottlenecks = metrics.get('bottlenecks', [])
            if bottlenecks:
                print(f"\n🔥 Bottlenecks ({len(bottlenecks)} nodes):")
                for node_id in bottlenecks[:5]:  # Show top 5
                    node_metric = metrics.get('node_metrics', {}).get(node_id, {})
                    duration = node_metric.get('duration_ms', 0)
                    node_type = node_metric.get('node_type', 'unknown')
                    print(f"  • {node_id} ({node_type}): {duration:.0f}ms")
        
        # Show parallelizable groups
        if not bottlenecks_only:
            parallelizable = metrics.get('parallelizable_groups', [])
            if parallelizable:
                print(f"\n⚡ Parallelizable Groups ({len(parallelizable)} groups):")
                for i, group in enumerate(parallelizable[:3], 1):  # Show top 3
                    print(f"  Group {i}: {', '.join(group)}")
    
    def _display_history_metrics(self, executions, bottlenecks_only, optimizations_only):
        """Display metrics history for multiple executions."""
        print("\n📈 Execution History Metrics")
        print("=" * 60)
        
        for execution in executions:
            print(f"\n▶ Execution {execution['id']}")
            print(f"  Status: {execution['status']}")
            print(f"  Started: {execution.get('startedAt', 'N/A')}")
            print(f"  Duration: {execution.get('durationSeconds', 0):.2f}s")
            
            metrics = execution.get('metrics')
            if metrics:
                if not optimizations_only:
                    bottlenecks = metrics.get('bottlenecks', [])
                    if bottlenecks:
                        print(f"  Bottlenecks: {len(bottlenecks)} nodes")
                
                if not bottlenecks_only:
                    parallelizable = metrics.get('parallelizable_groups', [])
                    if parallelizable:
                        print(f"  Parallelizable: {len(parallelizable)} groups")
            else:
                print("  No metrics available")
