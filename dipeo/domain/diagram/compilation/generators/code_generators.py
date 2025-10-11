"""Generator for code_job nodes."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator


class CodeJobNodeGenerator(BaseNodeGenerator):
    """Generator for code_job nodes (inline Python code execution)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for code_job node.

        Args:
            node: The code_job node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Code Job")
        code = node.data.get("code", "") if hasattr(node, "data") else getattr(node, "code", "")
        indent = self.context.get_indent()

        self._add_comment(label)

        # Add code lines with proper indentation
        for line in code.split("\n"):
            if line.strip():
                self.context.add_main_code(f"{indent}{line}")

        self._add_blank_line()
