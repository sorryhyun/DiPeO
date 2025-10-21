"""Convert DiPeO diagrams to standalone Python scripts."""

from pathlib import Path
from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators import (
    CodeJobNodeGenerator,
    ConditionNodeGenerator,
    DbNodeGenerator,
    EndpointNodeGenerator,
    PersonJobNodeGenerator,
    StartNodeGenerator,
    UserResponseNodeGenerator,
)
from dipeo.domain.diagram.compilation.generators.base import CompilationContext


class PythonDiagramCompiler:
    """Exports DiPeO diagrams to standalone Python scripts.

    Supports simplified export focusing on:
    - LLM calls (person_job nodes)
    - DB read/write (db nodes)
    - Code execution (code_job nodes)
    - Control flow (condition, start, endpoint)

    Does not include DB state management or monitor logic.
    """

    def __init__(self):
        self.context: CompilationContext | None = None
        self.visited_nodes = set()
        self.loops = []

    def export(self, diagram: DomainDiagram, output_path: str) -> bool:
        """Export diagram to Python script.

        Args:
            diagram: The domain diagram to export
            output_path: Path to write the Python script

        Returns:
            True if export successful, False otherwise
        """
        try:
            self.context = CompilationContext()
            self.visited_nodes = set()
            self.loops = []

            start_nodes = [n for n in diagram.nodes if n.type == "start"]
            if not start_nodes:
                print("❌ No start node found in diagram")
                return False

            execution_order = self._build_execution_order(diagram, start_nodes[0])

            if self.loops:
                self._generate_with_loops(diagram, execution_order)
            else:
                for node in execution_order:
                    self._generate_node_code(node, diagram)

            script = self._build_script(diagram)

            Path(output_path).write_text(script)
            print(f"✅ Exported diagram to {output_path}")
            return True

        except Exception as e:
            print(f"❌ Export failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _build_execution_order(self, diagram: DomainDiagram, start_node) -> list:
        """Build execution order and detect loops."""
        self._detect_loops(diagram, start_node)

        order = []
        to_visit = [start_node]
        visited = set()

        while to_visit:
            node = to_visit.pop(0)
            if node.id in visited:
                continue

            visited.add(node.id)
            order.append(node)

            outgoing = [a for a in diagram.arrows if a.source.startswith(f"{node.id}_")]

            for arrow in outgoing:
                target_handle = arrow.target
                target_node_id = (
                    "_".join(target_handle.split("_")[:-2])
                    if "_" in target_handle
                    else target_handle
                )

                target_node = next((n for n in diagram.nodes if n.id == target_node_id), None)
                if target_node and target_node.id not in visited:
                    to_visit.append(target_node)

        return order

    def _detect_loops(self, diagram: DomainDiagram, start_node):
        """Detect loops using back-edge detection."""
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if node.id in rec_stack:
                # Found a back-edge - this is a loop!
                loop_start_idx = path.index(node.id)
                loop_nodes = path[loop_start_idx:]

                # Find the condition node in the loop
                condition_node = None
                for node_id in loop_nodes:
                    n = next((n for n in diagram.nodes if n.id == node_id), None)
                    if n:
                        node_type = str(getattr(n, "type", "")).replace("NodeType.", "").lower()
                        if node_type == "condition":
                            condition_node = n
                            break

                if condition_node:
                    self.loops.append(
                        {"nodes": loop_nodes, "condition": condition_node, "entry": node.id}
                    )
                return

            if node.id in visited:
                return

            visited.add(node.id)
            rec_stack.add(node.id)
            path.append(node.id)

            outgoing = [a for a in diagram.arrows if a.source.startswith(f"{node.id}_")]

            for arrow in outgoing:
                target_handle = arrow.target
                target_node_id = (
                    "_".join(target_handle.split("_")[:-2])
                    if "_" in target_handle
                    else target_handle
                )
                target_node = next((n for n in diagram.nodes if n.id == target_node_id), None)

                if target_node:
                    dfs(target_node, path.copy())

            rec_stack.remove(node.id)

        dfs(start_node, [])

    def _generate_with_loops(self, diagram: DomainDiagram, execution_order: list):
        """Generate code with loop structures."""
        if not self.loops:
            return

        loop = self.loops[0]
        loop_node_ids = set(loop["nodes"])
        condition_node = loop["condition"]

        max_iterations = 10
        for node_id in loop["nodes"]:
            node = next((n for n in diagram.nodes if n.id == node_id), None)
            if node:
                node_type = str(getattr(node, "type", "")).replace("NodeType.", "").lower()
                if node_type == "person_job":
                    if hasattr(node, "data"):
                        max_iterations = node.data.get("max_iteration", 10)
                    else:
                        max_iterations = getattr(node, "max_iteration", 10)
                    break

        for node in execution_order:
            if node.id not in loop_node_ids:
                self._generate_node_code(node, diagram)
            else:
                break

        self.context.add_main_code(f"    # Loop: max {max_iterations} iterations")
        self.context.add_main_code("    iteration_count = 0")
        self.context.add_main_code(f"    while iteration_count < {max_iterations}:")
        self.context.indent_level = 2

        for node in execution_order:
            if node.id in loop_node_ids and node.id != condition_node.id:
                self._generate_node_code(node, diagram)

        self.context.add_main_code("        iteration_count += 1")
        self.context.add_main_code("")

        self.context.indent_level = 1

        condtrue_arrows = [
            a for a in diagram.arrows if a.source == f"{condition_node.id}_condtrue_output"
        ]
        if condtrue_arrows:
            target_handle = condtrue_arrows[0].target
            target_node_id = (
                "_".join(target_handle.split("_")[:-2]) if "_" in target_handle else target_handle
            )

            visited = set(loop_node_ids)
            to_visit = [target_node_id]

            while to_visit:
                node_id = to_visit.pop(0)
                if node_id in visited:
                    continue

                visited.add(node_id)
                node = next((n for n in diagram.nodes if n.id == node_id), None)
                if node:
                    self._generate_node_code(node, diagram)

                    outgoing = [a for a in diagram.arrows if a.source.startswith(f"{node.id}_")]
                    for arrow in outgoing:
                        target_handle = arrow.target
                        next_node_id = (
                            "_".join(target_handle.split("_")[:-2])
                            if "_" in target_handle
                            else target_handle
                        )
                        if next_node_id not in visited:
                            to_visit.append(next_node_id)

    def _generate_node_code(self, node, diagram: DomainDiagram):
        """Generate code for a specific node by delegating to appropriate generator.

        Args:
            node: The node to generate code for
            diagram: The full diagram
        """
        node_type = str(node.type) if hasattr(node.type, "value") else node.type
        if hasattr(node.type, "value"):
            node_type = node.type.value

        generator = None
        if node_type == "start":
            generator = StartNodeGenerator(self.context)
        elif node_type == "code_job":
            generator = CodeJobNodeGenerator(self.context)
        elif node_type == "person_job":
            generator = PersonJobNodeGenerator(self.context)
        elif node_type == "condition":
            generator = ConditionNodeGenerator(self.context)
        elif node_type == "endpoint":
            generator = EndpointNodeGenerator(self.context)
        elif node_type == "db":
            generator = DbNodeGenerator(self.context)
        elif node_type == "user_response":
            generator = UserResponseNodeGenerator(self.context)
        else:
            indent = self.context.get_indent()
            self.context.add_main_code(f"{indent}# TODO: Unsupported node type: {node_type}")

        if generator:
            generator.generate(node, diagram)

    def _build_script(self, diagram: DomainDiagram) -> str:
        """Build the final Python script.

        Args:
            diagram: The domain diagram being compiled

        Returns:
            The complete Python script as a string
        """
        lines = []

        # Header comment
        lines.append("#!/usr/bin/env python3")
        lines.append('"""')
        lines.append("Generated by DiPeO Diagram-to-Python Exporter")
        lines.append("This is a standalone Python script that can be run without DiPeO.")
        lines.append("")
        lines.append("To run: python <script>.py")
        lines.append('"""')
        lines.append("")

        lines.extend(sorted(self.context.imports))
        lines.append("")
        lines.append("")

        lines.append("async def main():")
        lines.append('    """Main execution function."""')

        if self.context.init_code:
            lines.append("")
            lines.append("    # Initialize clients")
            lines.extend(self.context.init_code)

        lines.append("")

        lines.extend(self.context.main_code)

        lines.append('    print("✅ Execution complete")')
        lines.append("")
        lines.append("")

        lines.append('if __name__ == "__main__":')
        lines.append("    asyncio.run(main())")
        lines.append("")

        return "\n".join(lines)
