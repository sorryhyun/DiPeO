"""Generator for control flow nodes (condition)."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator


class ConditionNodeGenerator(BaseNodeGenerator):
    """Generator for condition nodes (if/else logic)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for condition node.

        Args:
            node: The condition node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Condition")
        condition_type = (
            node.data.get("condition_type")
            if hasattr(node, "data")
            else getattr(node, "condition_type", None)
        )

        self.context.add_main_code(f"    # {label}")

        if condition_type == "custom":
            expression = (
                node.data.get("expression", "True")
                if hasattr(node, "data")
                else getattr(node, "expression", "True")
            )
            self.context.add_main_code(f"    if {expression}:")

            condtrue_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condtrue"]
            condfalse_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condfalse"]

            if condtrue_arrows:
                self.context.add_main_code("        # condtrue path")
                self.context.add_main_code("        pass  # Continue to next node")

            if condfalse_arrows:
                self.context.add_main_code("    else:")
                self.context.add_main_code("        # condfalse path")
                self.context.add_main_code("        pass  # Loop back or alternative path")
        else:
            self.context.add_main_code(
                f"    # TODO: Condition type '{condition_type}' not yet supported"
            )

        self._add_blank_line()
