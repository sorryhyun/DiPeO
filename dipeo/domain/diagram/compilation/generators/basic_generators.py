"""Generators for basic nodes (start, endpoint)."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator


class StartNodeGenerator(BaseNodeGenerator):
    """Generator for start nodes."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for start node.

        Args:
            node: The start node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Start")
        indent = self.context.get_indent()

        self._add_comment(label)
        self.context.add_main_code(f'{indent}print("Starting execution...")')
        self._add_blank_line()


class EndpointNodeGenerator(BaseNodeGenerator):
    """Generator for endpoint nodes."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for endpoint node.

        Args:
            node: The endpoint node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Endpoint")
        save_to_file = (
            node.data.get("save_to_file", False)
            if hasattr(node, "data")
            else getattr(node, "save_to_file", False)
        )
        file_path = (
            node.data.get("file_path") or node.data.get("file_name", "output.txt")
            if hasattr(node, "data")
            else getattr(node, "file_path", "output.txt")
        )
        indent = self.context.get_indent()

        self._add_comment(label)

        if save_to_file:
            self.context.add_import("from pathlib import Path")
            self.context.add_main_code(f"{indent}# Save result to file")
            self.context.add_main_code(f'{indent}output_path = Path("{file_path}")')
            self.context.add_main_code(
                f"{indent}output_path.parent.mkdir(parents=True, exist_ok=True)"
            )

            # Find what to save (last node output or 'result' variable)
            if self.context.node_outputs:
                last_output = list(self.context.node_outputs.values())[-1]
                self.context.add_main_code(f"{indent}output_path.write_text(str({last_output}))")
            else:
                self.context.add_main_code(f"{indent}output_path.write_text(str(result))")

            self.context.add_main_code(f'{indent}print(f"✅ Saved output to {{output_path}}")')
        else:
            self.context.add_main_code(f"{indent}# Output endpoint")
            if self.context.node_outputs:
                last_output = list(self.context.node_outputs.values())[-1]
                self.context.add_main_code(f'{indent}print(f"✅ Result: {{{last_output}}}")')

        self._add_blank_line()
