"""AST processing framework for unified TypeScript AST traversal and extraction.

This module provides a comprehensive framework for working with TypeScript AST data:
- Walker: Traverse AST data with visitor pattern
- Filters: Filter files and nodes by patterns
- Extractors: Extract specific node types with type-safe interfaces

Example usage:
    # Using extractors directly
    from dipeo.infrastructure.codegen.ir_builders.ast import InterfaceExtractor

    extractor = InterfaceExtractor()
    interfaces = extractor.extract(ast_data, suffix="Config")

    # Using walker with visitor
    from dipeo.infrastructure.codegen.ir_builders.ast import ASTWalker, ASTVisitor

    class MyVisitor(ASTVisitor):
        def visit_interface(self, node, file_path, context):
            print(f"Found interface: {node['name']}")

    walker = ASTWalker(ast_data)
    walker.walk(MyVisitor())
"""

from dipeo.infrastructure.codegen.ir_builders.ast.extractors import (
    BrandedScalarExtractor,
    ConstantExtractor,
    EnumExtractor,
    GraphQLInputTypeExtractor,
    InterfaceExtractor,
    TypeAliasExtractor,
)
from dipeo.infrastructure.codegen.ir_builders.ast.filters import (
    FileFilter,
    NodeFilter,
    and_filter,
    not_filter,
    or_filter,
    prefix_filter,
    regex_filter,
    suffix_filter,
)
from dipeo.infrastructure.codegen.ir_builders.ast.walker import ASTVisitor, ASTWalker

__all__ = [
    # Walker
    "ASTWalker",
    "ASTVisitor",
    # Filters
    "FileFilter",
    "NodeFilter",
    "prefix_filter",
    "suffix_filter",
    "regex_filter",
    "and_filter",
    "or_filter",
    "not_filter",
    # Extractors
    "InterfaceExtractor",
    "EnumExtractor",
    "TypeAliasExtractor",
    "ConstantExtractor",
    "BrandedScalarExtractor",
    "GraphQLInputTypeExtractor",
]