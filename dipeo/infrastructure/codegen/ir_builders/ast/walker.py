"""AST walker and visitor pattern implementation for TypeScript AST traversal.

This module provides a flexible visitor pattern for traversing TypeScript AST data.
The ASTWalker handles iteration over files and nodes, while ASTVisitor subclasses
define custom behavior for each node type.

Example:
    class MyVisitor(ASTVisitor):
        def __init__(self):
            super().__init__()
            self.found_interfaces = []

        def visit_interface(self, node, file_path, context):
            self.found_interfaces.append(node)
            return node  # Return modified node or None to skip

    walker = ASTWalker(ast_data)
    visitor = MyVisitor()
    walker.walk(visitor)
    print(f"Found {len(visitor.found_interfaces)} interfaces")
"""

from __future__ import annotations

from typing import Any, Optional


class ASTVisitor:
    """Base class for AST visitors.

    Subclasses should override visit methods for node types they want to process.
    Each visit method receives:
    - node: The AST node data
    - file_path: Path to the source file
    - context: Dictionary for passing state between visits

    Pre/post hooks are called before and after each visit method.
    """

    def __init__(self):
        """Initialize visitor with empty context."""
        self.context: dict[str, Any] = {}

    # Pre/post hooks
    def pre_visit(self, node_type: str, node: dict[str, Any], file_path: str) -> bool:
        """Called before visiting a node.

        Args:
            node_type: Type of node (interface, enum, etc.)
            node: The node data
            file_path: Path to source file

        Returns:
            False to skip this node, True to continue
        """
        return True

    def post_visit(self, node_type: str, node: dict[str, Any], file_path: str, result: Any) -> None:
        """Called after visiting a node.

        Args:
            node_type: Type of node
            node: The node data
            file_path: Path to source file
            result: Result returned by visit method
        """
        pass

    # Visit methods for each node type
    def visit_interface(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit an interface node.

        Args:
            node: Interface node data with 'name', 'properties', 'extends'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node

    def visit_enum(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit an enum node.

        Args:
            node: Enum node data with 'name', 'members'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node

    def visit_type_alias(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit a type alias node.

        Args:
            node: Type alias node data with 'name', 'type'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node

    def visit_constant(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit a constant node.

        Args:
            node: Constant node data with 'name', 'value', 'type'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node

    def visit_branded_scalar(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit a branded scalar node.

        Args:
            node: Branded scalar node data with 'name', 'baseType'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node

    def visit_type(
        self, node: dict[str, Any], file_path: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Visit a generic type node.

        Args:
            node: Type node data with 'name', 'type'
            file_path: Path to source file
            context: Shared context dictionary

        Returns:
            Modified node or None
        """
        return node


class ASTWalker:
    """Walker for traversing TypeScript AST data with visitor pattern.

    The walker handles iteration over files and nodes, delegating to visitor
    methods for processing. It supports filtering files and managing traversal context.

    Example:
        walker = ASTWalker(ast_data)
        walker.walk(MyVisitor())

        # With file filter
        walker = ASTWalker(ast_data, file_filter=lambda path: 'node-specs' in path)
        walker.walk(MyVisitor())
    """

    def __init__(self, ast_data: dict[str, Any], file_filter: callable | None = None):
        """Initialize walker with AST data.

        Args:
            ast_data: Dictionary mapping file paths to AST data
            file_filter: Optional callable to filter files (receives file_path, returns bool)
        """
        self.ast_data = ast_data
        self.file_filter = file_filter

    def walk(self, visitor: ASTVisitor) -> None:
        """Walk the AST with the given visitor.

        Args:
            visitor: ASTVisitor instance to use for processing nodes
        """
        for file_path, file_data in self.ast_data.items():
            # Apply file filter if provided
            if self.file_filter and not self.file_filter(file_path):
                continue

            if not isinstance(file_data, dict):
                continue

            # Visit each node type
            self._visit_nodes(visitor, file_data, file_path, "interfaces", "visit_interface")
            self._visit_nodes(visitor, file_data, file_path, "enums", "visit_enum")
            self._visit_nodes(visitor, file_data, file_path, "typeAliases", "visit_type_alias")
            self._visit_nodes(visitor, file_data, file_path, "constants", "visit_constant")
            self._visit_nodes(
                visitor, file_data, file_path, "brandedScalars", "visit_branded_scalar"
            )
            self._visit_nodes(visitor, file_data, file_path, "types", "visit_type")

    def _visit_nodes(
        self,
        visitor: ASTVisitor,
        file_data: dict[str, Any],
        file_path: str,
        node_list_key: str,
        visit_method_name: str,
    ) -> None:
        """Visit all nodes of a specific type.

        Args:
            visitor: ASTVisitor instance
            file_data: AST data for current file
            file_path: Path to source file
            node_list_key: Key for node list in file_data (e.g., 'interfaces')
            visit_method_name: Name of visitor method to call (e.g., 'visit_interface')
        """
        nodes = file_data.get(node_list_key, [])
        visit_method = getattr(visitor, visit_method_name)

        for node in nodes:
            if not isinstance(node, dict):
                continue

            # Call pre-visit hook
            node_type = node_list_key.rstrip("s")  # Remove trailing 's'
            if not visitor.pre_visit(node_type, node, file_path):
                continue

            # Call visit method
            result = visit_method(node, file_path, visitor.context)

            # Call post-visit hook
            visitor.post_visit(node_type, node, file_path, result)


class CollectorVisitor(ASTVisitor):
    """Convenience visitor that collects all visited nodes of specific types.

    Example:
        collector = CollectorVisitor(collect_types=['interface', 'enum'])
        walker.walk(collector)
        print(collector.collected['interface'])  # All interfaces
        print(collector.collected['enum'])        # All enums
    """

    def __init__(self, collect_types: list[str] | None = None):
        """Initialize collector.

        Args:
            collect_types: List of node types to collect (e.g., ['interface', 'enum'])
                         If None, collects all types
        """
        super().__init__()
        self.collect_types = collect_types
        self.collected: dict[str, list[dict[str, Any]]] = {}

    def _should_collect(self, node_type: str) -> bool:
        """Check if node type should be collected."""
        if self.collect_types is None:
            return True
        return node_type in self.collect_types

    def _collect(self, node_type: str, node: dict[str, Any], file_path: str) -> None:
        """Collect a node."""
        if self._should_collect(node_type):
            if node_type not in self.collected:
                self.collected[node_type] = []
            node_with_file = {**node, "file": file_path}
            self.collected[node_type].append(node_with_file)

    def visit_interface(self, node, file_path, context):
        self._collect("interface", node, file_path)
        return node

    def visit_enum(self, node, file_path, context):
        self._collect("enum", node, file_path)
        return node

    def visit_type_alias(self, node, file_path, context):
        self._collect("type_alias", node, file_path)
        return node

    def visit_constant(self, node, file_path, context):
        self._collect("constant", node, file_path)
        return node

    def visit_branded_scalar(self, node, file_path, context):
        self._collect("branded_scalar", node, file_path)
        return node

    def visit_type(self, node, file_path, context):
        self._collect("type", node, file_path)
        return node
