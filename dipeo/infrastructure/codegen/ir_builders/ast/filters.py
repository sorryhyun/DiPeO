"""Filter utilities for AST traversal and node selection.

This module provides flexible filtering capabilities for both files and AST nodes:
- FileFilter: Filter files by path patterns
- NodeFilter: Filter nodes by name, type, or custom predicates
- Filter composition: Combine filters with AND, OR, NOT logic

Example:
    # Filter files by pattern
    file_filter = FileFilter(patterns=['**/node-specs/**/*.ts'])
    matching_files = file_filter.filter(ast_data)

    # Filter nodes by suffix
    node_filter = suffix_filter('Config')
    configs = node_filter.filter_nodes(interfaces)

    # Compose filters
    combined = and_filter(
        suffix_filter('Config'),
        not_filter(prefix_filter('Internal'))
    )
"""

from __future__ import annotations

import re
from collections.abc import Callable
from fnmatch import fnmatch
from typing import Any, Optional

# ============================================================================
# FILE FILTERS
# ============================================================================


class FileFilter:
    """Filter files by path patterns.

    Supports:
    - Glob patterns (*, **, ?)
    - Regex patterns
    - Custom predicates

    Example:
        # Glob pattern
        filter = FileFilter(patterns=['**/node-specs/**'])
        files = filter.filter(ast_data)

        # Regex pattern
        filter = FileFilter(regex=r'node-specs/.*\\.ts$')

        # Custom predicate
        filter = FileFilter(predicate=lambda path: 'test' not in path)
    """

    def __init__(
        self,
        patterns: list[str] | None = None,
        regex: str | re.Pattern | None = None,
        predicate: Callable[[str], bool] | None = None,
    ):
        """Initialize file filter.

        Args:
            patterns: List of glob patterns (e.g., ['**/*.ts', 'src/**'])
            regex: Regex pattern or compiled Pattern object
            predicate: Custom predicate function (receives file path, returns bool)
        """
        self.patterns = patterns or []
        self.regex = re.compile(regex) if isinstance(regex, str) else regex
        self.predicate = predicate

    def matches(self, file_path: str) -> bool:
        """Check if file path matches filter criteria.

        Args:
            file_path: Path to check

        Returns:
            True if file matches, False otherwise
        """
        # Check glob patterns
        if self.patterns:
            if not any(fnmatch(file_path, pattern) for pattern in self.patterns):
                return False

        # Check regex
        if self.regex:
            if not self.regex.search(file_path):
                return False

        # Check predicate
        if self.predicate:
            if not self.predicate(file_path):
                return False

        return True

    def filter(self, ast_data: dict[str, Any]) -> dict[str, Any]:
        """Filter AST data by file paths.

        Args:
            ast_data: Dictionary mapping file paths to AST data

        Returns:
            Filtered dictionary with only matching files
        """
        return {
            file_path: file_data
            for file_path, file_data in ast_data.items()
            if self.matches(file_path)
        }


# ============================================================================
# NODE FILTERS
# ============================================================================


class NodeFilter:
    """Filter AST nodes by various criteria.

    Supports:
    - Name patterns (prefix, suffix, contains)
    - Regex matching on node names
    - Custom predicates on node data

    Example:
        # Filter by suffix
        filter = NodeFilter(suffix='Config')
        configs = filter.filter_nodes(interfaces)

        # Filter by regex
        filter = NodeFilter(regex=r'^User.*')
        user_nodes = filter.filter_nodes(nodes)

        # Custom predicate
        filter = NodeFilter(predicate=lambda node: len(node.get('properties', [])) > 5)
        large_interfaces = filter.filter_nodes(interfaces)
    """

    def __init__(
        self,
        prefix: str | None = None,
        suffix: str | None = None,
        contains: str | None = None,
        regex: str | re.Pattern | None = None,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ):
        """Initialize node filter.

        Args:
            prefix: Required prefix for node names
            suffix: Required suffix for node names
            contains: Required substring in node names
            regex: Regex pattern for node names
            predicate: Custom predicate function (receives node dict, returns bool)
        """
        self.prefix = prefix
        self.suffix = suffix
        self.contains = contains
        self.regex = re.compile(regex) if isinstance(regex, str) else regex
        self.predicate = predicate

    def matches(self, node: dict[str, Any]) -> bool:
        """Check if node matches filter criteria.

        Args:
            node: Node dictionary to check

        Returns:
            True if node matches, False otherwise
        """
        node_name = node.get("name", "")

        # Check prefix
        if self.prefix and not node_name.startswith(self.prefix):
            return False

        # Check suffix
        if self.suffix and not node_name.endswith(self.suffix):
            return False

        # Check contains
        if self.contains and self.contains not in node_name:
            return False

        # Check regex
        if self.regex and not self.regex.search(node_name):
            return False

        # Check predicate
        if self.predicate and not self.predicate(node):
            return False

        return True

    def filter_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter list of nodes.

        Args:
            nodes: List of node dictionaries

        Returns:
            Filtered list with only matching nodes
        """
        return [node for node in nodes if self.matches(node)]


# ============================================================================
# FILTER COMPOSITION
# ============================================================================


class CompositeNodeFilter(NodeFilter):
    """Composite filter that combines multiple node filters."""

    def __init__(self, filters: list[NodeFilter], operator: str = "and"):
        """Initialize composite filter.

        Args:
            filters: List of NodeFilter instances to combine
            operator: How to combine filters ('and', 'or')
        """
        super().__init__()
        self.filters = filters
        self.operator = operator.lower()

    def matches(self, node: dict[str, Any]) -> bool:
        """Check if node matches composite filter."""
        if self.operator == "and":
            return all(f.matches(node) for f in self.filters)
        elif self.operator == "or":
            return any(f.matches(node) for f in self.filters)
        return False


class NotNodeFilter(NodeFilter):
    """Negation filter that inverts another filter."""

    def __init__(self, filter: NodeFilter):
        """Initialize negation filter.

        Args:
            filter: NodeFilter instance to negate
        """
        super().__init__()
        self.filter = filter

    def matches(self, node: dict[str, Any]) -> bool:
        """Check if node does NOT match the wrapped filter."""
        return not self.filter.matches(node)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def prefix_filter(prefix: str) -> NodeFilter:
    """Create a filter for nodes with names starting with prefix.

    Args:
        prefix: Required prefix

    Returns:
        NodeFilter instance

    Example:
        filter = prefix_filter('User')
        user_nodes = filter.filter_nodes(nodes)
    """
    return NodeFilter(prefix=prefix)


def suffix_filter(suffix: str) -> NodeFilter:
    """Create a filter for nodes with names ending with suffix.

    Args:
        suffix: Required suffix

    Returns:
        NodeFilter instance

    Example:
        filter = suffix_filter('Config')
        configs = filter.filter_nodes(nodes)
    """
    return NodeFilter(suffix=suffix)


def regex_filter(pattern: str | re.Pattern) -> NodeFilter:
    """Create a filter for nodes matching a regex pattern.

    Args:
        pattern: Regex pattern or compiled Pattern

    Returns:
        NodeFilter instance

    Example:
        filter = regex_filter(r'^User.*Config$')
        matches = filter.filter_nodes(nodes)
    """
    return NodeFilter(regex=pattern)


def and_filter(*filters: NodeFilter) -> CompositeNodeFilter:
    """Create a filter that matches nodes passing ALL filters.

    Args:
        *filters: NodeFilter instances to combine

    Returns:
        CompositeNodeFilter with AND logic

    Example:
        filter = and_filter(
            prefix_filter('User'),
            suffix_filter('Config')
        )
    """
    return CompositeNodeFilter(list(filters), operator="and")


def or_filter(*filters: NodeFilter) -> CompositeNodeFilter:
    """Create a filter that matches nodes passing ANY filter.

    Args:
        *filters: NodeFilter instances to combine

    Returns:
        CompositeNodeFilter with OR logic

    Example:
        filter = or_filter(
            suffix_filter('Config'),
            suffix_filter('Props')
        )
    """
    return CompositeNodeFilter(list(filters), operator="or")


def not_filter(filter: NodeFilter) -> NotNodeFilter:
    """Create a filter that inverts another filter.

    Args:
        filter: NodeFilter instance to negate

    Returns:
        NotNodeFilter instance

    Example:
        filter = not_filter(prefix_filter('Internal'))
    """
    return NotNodeFilter(filter)


# ============================================================================
# PRESET FILTERS
# ============================================================================


# Common file patterns
NODE_SPECS_FILES = FileFilter(patterns=["**/node-specs/**/*.ts"])
DOMAIN_MODEL_FILES = FileFilter(patterns=["**/domain-models/**/*.ts"])
GRAPHQL_FILES = FileFilter(patterns=["**/graphql-inputs.ts", "**/query-definitions/**/*.ts"])

# Common node patterns
CONFIG_INTERFACES = suffix_filter("Config")
PROPS_INTERFACES = suffix_filter("Props")
INPUT_TYPES = suffix_filter("Input")
ID_TYPES = suffix_filter("ID")
