"""Generators for data-related nodes (db, user_response)."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator


class DbNodeGenerator(BaseNodeGenerator):
    """Generator for db nodes (file read/write operations)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for db node (file operations).

        Args:
            node: The db node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "DB")
        operation = (
            node.data.get("operation")
            if hasattr(node, "data")
            else getattr(node, "operation", None)
        )
        file_data = node.data.get("file") if hasattr(node, "data") else getattr(node, "file", [])
        file_paths = file_data if isinstance(file_data, list) else [file_data]
        indent = self.context.get_indent()

        self._add_comment(label)
        self.context.add_import("from pathlib import Path")

        if operation == "read":
            self._generate_read_operation(node, file_paths, indent)
        elif operation == "write":
            self._generate_write_operation(file_paths, indent)
        elif operation == "append":
            self._generate_append_operation(file_paths, indent)

        self._add_blank_line()

    def _generate_read_operation(self, node: Any, file_paths: list[str], indent: str) -> None:
        """Generate code for file read operation.

        Args:
            node: The db node
            file_paths: List of file paths to read
            indent: Current indentation string
        """
        for file_path in file_paths:
            var_name = self._get_node_var_name(node)
            self.context.add_main_code(f'{indent}{var_name} = Path("{file_path}").read_text()')
            self.context.set_node_output(node.id, var_name)

    def _generate_write_operation(self, file_paths: list[str], indent: str) -> None:
        """Generate code for file write operation.

        Args:
            file_paths: List of file paths to write
            indent: Current indentation string
        """
        for file_path in file_paths:
            # Determine what to write
            if self.context.node_outputs:
                last_output = list(self.context.node_outputs.values())[-1]
                content_var = last_output
            else:
                content_var = "content"

            self.context.add_main_code(f'{indent}db_path = Path("{file_path}")')
            self.context.add_main_code(f"{indent}db_path.parent.mkdir(parents=True, exist_ok=True)")
            self.context.add_main_code(f"{indent}db_path.write_text(str({content_var}))")

    def _generate_append_operation(self, file_paths: list[str], indent: str) -> None:
        """Generate code for file append operation.

        Args:
            file_paths: List of file paths to append to
            indent: Current indentation string
        """
        for file_path in file_paths:
            if self.context.node_outputs:
                last_output = list(self.context.node_outputs.values())[-1]
                content_var = last_output
            else:
                content_var = "content"

            self.context.add_main_code(f'{indent}with open("{file_path}", "a") as f:')
            self.context.add_main_code(f"{indent}    f.write(str({content_var}))")


class UserResponseNodeGenerator(BaseNodeGenerator):
    """Generator for user_response nodes (user input)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for user_response node (user input).

        Args:
            node: The user_response node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "User Input")
        prompt = (
            node.data.get("prompt", "Enter value: ")
            if hasattr(node, "data")
            else getattr(node, "prompt", "Enter value: ")
        )
        timeout = (
            node.data.get("timeout") if hasattr(node, "data") else getattr(node, "timeout", None)
        )
        indent = self.context.get_indent()

        self._add_comment(label)

        if timeout:
            self.context.add_main_code(
                f"{indent}# Note: timeout={timeout}s not implemented in export"
            )

        var_name = self._get_node_var_name(node)
        self.context.add_main_code(f"{indent}{var_name} = input({prompt!r})")
        self._add_blank_line()

        self.context.set_node_output(node.id, var_name)
