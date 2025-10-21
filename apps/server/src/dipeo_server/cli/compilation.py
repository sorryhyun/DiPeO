"""Diagram compilation and validation functionality."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

from dipeo.application.bootstrap import Container
from dipeo.config.base_logger import get_module_logger

from .core import DiagramLoader

logger = get_module_logger(__name__)


class DiagramCompiler:
    """Handles diagram compilation and validation."""

    def __init__(self, container: Container):
        self.container = container
        self.diagram_loader = DiagramLoader()

    async def compile_diagram(
        self,
        diagram_path: str | None,
        format_type: str | None = None,
        check_only: bool = False,
        output_json: bool = False,
        use_stdin: bool = False,
        push_as: str | None = None,
        target_dir: str | None = None,
    ) -> bool:
        """Compile and validate diagram without executing it.

        Args:
            diagram_path: Path to diagram file (optional if use_stdin=True)
            format_type: Diagram format (light, native, readable)
            check_only: Only validate structure
            output_json: Output results as JSON
            use_stdin: Read diagram content from stdin
            push_as: Push compiled diagram with specified filename (works with --stdin)
            target_dir: Target directory for push (default: projects/mcp-diagrams/)
        """
        temp_file = None
        source_path = diagram_path

        try:
            from dipeo.domain.diagram.compilation import DomainDiagramCompiler

            if use_stdin:
                if not format_type:
                    print(
                        "❌ Format type is required with --stdin (use --light, --native, or --readable)"
                    )
                    return False

                stdin_content = sys.stdin.read()
                if not stdin_content.strip():
                    print("❌ No content received from stdin")
                    return False

                suffix = ".yaml" if format_type in ["light", "readable"] else ".json"
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=suffix, delete=False
                ) as temp_file:
                    temp_file.write(stdin_content)
                    source_path = temp_file.name

                if not output_json:
                    print("📥 Reading diagram from stdin...")
            elif not diagram_path:
                print("❌ Either diagram path or --stdin is required")
                return False

            (
                domain_diagram,
                diagram_data,
                diagram_file_path,
            ) = await self.diagram_loader.load_and_deserialize(source_path, format_type)

            if not domain_diagram:
                print(f"❌ Failed to load diagram: {source_path}")
                return False

            compiler = DomainDiagramCompiler()
            result = compiler.compile_with_diagnostics(domain_diagram)

            if output_json:
                import json

                output = {
                    "valid": result.is_valid,
                    "errors": [
                        {
                            "phase": e.phase.name,
                            "message": e.message,
                            "severity": e.severity,
                            "node_id": str(e.node_id) if e.node_id else None,
                        }
                        for e in result.errors
                    ],
                    "warnings": [
                        {
                            "phase": w.phase.name,
                            "message": w.message,
                            "severity": w.severity,
                            "node_id": str(w.node_id) if w.node_id else None,
                        }
                        for w in result.warnings
                    ],
                }
                if result.diagram:
                    output["node_count"] = len(result.diagram.nodes)
                    output["edge_count"] = len(result.diagram.edges)
                print(json.dumps(output, indent=2))
            else:
                if result.is_valid:
                    display_path = "stdin" if use_stdin else source_path
                    print(f"✅ Diagram compiled successfully: {display_path}")
                    if result.diagram:
                        print(f"   Nodes: {len(result.diagram.nodes)}")
                        print(f"   Edges: {len(result.diagram.edges)}")
                else:
                    display_path = "stdin" if use_stdin else source_path
                    print(f"❌ Compilation failed: {display_path}")

                if result.warnings:
                    print(f"\n⚠️  Warnings ({len(result.warnings)}):")
                    for w in result.warnings:
                        print(f"   [{w.phase.name}] {w.message}")

                if result.errors:
                    print(f"\n❌ Errors ({len(result.errors)}):")
                    for e in result.errors:
                        print(f"   [{e.phase.name}] {e.message}")

            if result.is_valid and push_as:
                if target_dir:
                    push_dir = Path(target_dir)
                else:
                    push_dir = Path("projects/mcp-diagrams")

                push_dir.mkdir(parents=True, exist_ok=True)

                if format_type in ["light", "readable"]:
                    extension = ".yaml"
                else:
                    extension = ".json"

                if not push_as.endswith(extension):
                    target_filename = f"{push_as}{extension}"
                else:
                    target_filename = push_as

                target_file = push_dir / target_filename

                shutil.copy2(diagram_file_path, target_file)

                if not output_json:
                    print(f"\n✅ Pushed diagram to: {target_file}")
                    print(f"   Available via MCP server at: dipeo://diagrams/{target_filename}")

            return result.is_valid

        except Exception as e:
            logger.error(f"Diagram compilation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
