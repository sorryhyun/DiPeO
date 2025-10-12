"""Base class for node code generators."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.utils import indent_string, node_var_name


class CompilationContext:
    """Context object passed between generators during compilation.

    Attributes:
        imports: Set of import statements to include in the generated script
        init_code: List of initialization code lines (e.g., client creation)
        main_code: List of main execution code lines
        node_outputs: Mapping of node IDs to their output variable names
        indent_level: Current indentation level for code generation
    """

    def __init__(self):
        self.imports: set[str] = {"import asyncio"}
        self.init_code: list[str] = []
        self.main_code: list[str] = []
        self.node_outputs: dict[str, str] = {}
        self.indent_level: int = 1

    def add_import(self, import_statement: str) -> None:
        """Add an import statement to the generated script."""
        self.imports.add(import_statement)

    def add_init_code(self, code: str) -> None:
        """Add initialization code (runs before main execution)."""
        self.init_code.append(code)

    def add_main_code(self, code: str) -> None:
        """Add main execution code."""
        self.main_code.append(code)

    def get_indent(self) -> str:
        """Get current indentation string."""
        return indent_string(self.indent_level)

    def set_node_output(self, node_id: str, var_name: str) -> None:
        """Register a node's output variable name."""
        self.node_outputs[node_id] = var_name


class BaseNodeGenerator:
    """Base class for node-specific code generators.

    Each node type has its own generator that inherits from this class.
    """

    def __init__(self, context: CompilationContext):
        """Initialize generator with compilation context.

        Args:
            context: The compilation context containing imports, code, etc.
        """
        self.context = context

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for the given node.

        Args:
            node: The node to generate code for
            diagram: The full diagram (needed for context like arrows, persons)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def _get_node_label(self, node: Any, default: str = "Node") -> str:
        """Extract label from node data or attributes.

        Args:
            node: The node to extract label from
            default: Default label if none found

        Returns:
            The node's label
        """
        return (
            node.data.get("label", default)
            if hasattr(node, "data")
            else getattr(node, "label", default)
        )

    def _get_node_var_name(self, node: Any) -> str:
        """Generate a variable name for this node's output.

        Args:
            node: The node to generate variable name for

        Returns:
            A valid Python variable name
        """
        return node_var_name(node)

    def _add_comment(self, comment: str) -> None:
        """Add a comment line to the main code.

        Args:
            comment: The comment text (without # prefix)
        """
        indent = self.context.get_indent()
        self.context.add_main_code(f"{indent}# {comment}")

    def _add_blank_line(self) -> None:
        """Add a blank line to the main code."""
        self.context.add_main_code("")
