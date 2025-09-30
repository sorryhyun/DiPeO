"""Specialized extractors for TypeScript AST nodes.

This module provides type-safe extractor classes for different AST node types.
Each extractor consolidates extraction logic from utils.py into a reusable class.

Example:
    # Extract interfaces with suffix filter
    extractor = InterfaceExtractor(suffix='Config')
    configs = extractor.extract(ast_data)

    # Extract enums
    extractor = EnumExtractor()
    enums = extractor.extract(ast_data)

    # Extract with file filter
    from dipeo.infrastructure.codegen.ir_builders.ast.filters import FileFilter

    file_filter = FileFilter(patterns=['**/node-specs/**'])
    extractor = InterfaceExtractor(file_filter=file_filter)
    interfaces = extractor.extract(ast_data)
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.ast.filters import FileFilter, NodeFilter


# ============================================================================
# BASE EXTRACTOR
# ============================================================================


class BaseExtractor(ABC):
    """Base class for AST node extractors.

    Provides common extraction pattern:
    1. Filter files (optional)
    2. Extract nodes from matching files
    3. Filter nodes (optional)
    4. Transform to output format
    """

    def __init__(
        self,
        file_filter: Optional[FileFilter] = None,
        node_filter: Optional[NodeFilter] = None,
    ):
        """Initialize extractor.

        Args:
            file_filter: Optional filter for file paths
            node_filter: Optional filter for nodes
        """
        self.file_filter = file_filter
        self.node_filter = node_filter

    def extract(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract nodes from AST data.

        Args:
            ast_data: Dictionary mapping file paths to AST data

        Returns:
            List of extracted node dictionaries
        """
        # Apply file filter if provided
        if self.file_filter:
            ast_data = self.file_filter.filter(ast_data)

        results = []
        for file_path, file_data in ast_data.items():
            if not isinstance(file_data, dict):
                continue

            # Extract nodes from this file
            nodes = self._extract_from_file(file_data, file_path)

            # Apply node filter if provided
            if self.node_filter:
                nodes = self.node_filter.filter_nodes(nodes)

            results.extend(nodes)

        return results

    @abstractmethod
    def _extract_from_file(
        self, file_data: dict[str, Any], file_path: str
    ) -> list[dict[str, Any]]:
        """Extract nodes from a single file's AST data.

        Args:
            file_data: AST data for the file
            file_path: Path to the source file

        Returns:
            List of extracted nodes
        """
        pass


# ============================================================================
# SPECIALIZED EXTRACTORS
# ============================================================================


class InterfaceExtractor(BaseExtractor):
    """Extract TypeScript interfaces from AST data.

    Example:
        # Extract all interfaces
        extractor = InterfaceExtractor()
        interfaces = extractor.extract(ast_data)

        # Extract interfaces ending with 'Config'
        extractor = InterfaceExtractor(suffix='Config')
        configs = extractor.extract(ast_data)
    """

    def __init__(
        self,
        suffix: Optional[str] = None,
        file_filter: Optional[FileFilter] = None,
    ):
        """Initialize interface extractor.

        Args:
            suffix: Optional suffix to filter interface names
            file_filter: Optional filter for file paths
        """
        node_filter = NodeFilter(suffix=suffix) if suffix else None
        super().__init__(file_filter=file_filter, node_filter=node_filter)

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        interfaces = []
        for interface in file_data.get("interfaces", []):
            interfaces.append(
                {
                    "name": interface.get("name", ""),
                    "properties": interface.get("properties", []),
                    "extends": interface.get("extends", []),
                    "file": file_path,
                }
            )
        return interfaces


class EnumExtractor(BaseExtractor):
    """Extract TypeScript enums from AST data.

    Example:
        extractor = EnumExtractor()
        enums = extractor.extract(ast_data)
    """

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        enums = []
        for enum in file_data.get("enums", []):
            enums.append(
                {
                    "name": enum.get("name", ""),
                    "members": enum.get("members", []),
                    "file": file_path,
                }
            )
        return enums


class TypeAliasExtractor(BaseExtractor):
    """Extract TypeScript type aliases from AST data.

    Example:
        extractor = TypeAliasExtractor()
        type_aliases = extractor.extract(ast_data)
    """

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        type_aliases = []
        for type_alias in file_data.get("typeAliases", []):
            type_aliases.append(
                {
                    "name": type_alias.get("name", ""),
                    "type": type_alias.get("type"),
                    "file": file_path,
                }
            )
        return type_aliases


class ConstantExtractor(BaseExtractor):
    """Extract constants from AST data.

    Example:
        # Extract all constants
        extractor = ConstantExtractor()
        constants = extractor.extract(ast_data)

        # Extract constants matching pattern
        extractor = ConstantExtractor(pattern=r'^DEFAULT_.*')
        default_constants = extractor.extract(ast_data)
    """

    def __init__(
        self,
        pattern: Optional[str] = None,
        file_filter: Optional[FileFilter] = None,
    ):
        """Initialize constant extractor.

        Args:
            pattern: Optional regex pattern to filter constant names
            file_filter: Optional filter for file paths
        """
        node_filter = NodeFilter(regex=pattern) if pattern else None
        super().__init__(file_filter=file_filter, node_filter=node_filter)

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        constants = []
        for const in file_data.get("constants", []):
            constants.append(
                {
                    "name": const.get("name", ""),
                    "value": const.get("value"),
                    "type": const.get("type"),
                    "file": file_path,
                }
            )
        return constants


class BrandedScalarExtractor(BaseExtractor):
    """Extract branded scalar types from AST data.

    Branded scalars are types like:
    - type UserID = string & { readonly __brand: 'UserID' }
    - Explicitly marked brandedScalars in AST
    - Type aliases ending with ID

    Example:
        extractor = BrandedScalarExtractor()
        scalars = extractor.extract(ast_data)
    """

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        scalars = []
        seen_names = set()

        # Look for branded scalars in the AST
        for scalar in file_data.get("brandedScalars", []):
            scalar_name = scalar.get("name", "")
            if scalar_name and scalar_name not in seen_names:
                scalars.append(
                    {
                        "name": scalar_name,
                        "type": scalar.get("baseType", "string"),
                        "description": f"Branded scalar type for {scalar_name}",
                    }
                )
                seen_names.add(scalar_name)

        # Also look for NewType declarations that end with ID
        for type_alias in file_data.get("typeAliases", []):
            name = type_alias.get("name", "")
            if name.endswith("ID") and name not in seen_names:
                scalars.append(
                    {
                        "name": name,
                        "type": "string",
                        "description": f"Branded scalar type for {name}",
                    }
                )
                seen_names.add(name)

        # Look in types array for branded types (pattern: string & { readonly __brand: ... })
        for type_def in file_data.get("types", []):
            if isinstance(type_def, dict):
                type_name = type_def.get("name", "")
                type_value = type_def.get("type", "")
                # Check if it's a branded type pattern
                if "__brand" in type_value and type_name and type_name not in seen_names:
                    # Extract base type (usually "string" before the &)
                    base_type = "string"  # Default to string
                    if "string &" in type_value:
                        base_type = "string"
                    elif "number &" in type_value:
                        base_type = "number"

                    scalars.append(
                        {
                            "name": type_name,
                            "type": base_type,
                            "description": f"Branded scalar type for {type_name}",
                        }
                    )
                    seen_names.add(type_name)

        return scalars


class GraphQLInputTypeExtractor(BaseExtractor):
    """Extract GraphQL input types from AST data.

    Looks for type aliases ending with 'Input' from graphql-inputs.ts

    Example:
        extractor = GraphQLInputTypeExtractor()
        input_types = extractor.extract(ast_data)
    """

    def __init__(self):
        """Initialize GraphQL input type extractor."""
        # Only process graphql-inputs files
        file_filter = FileFilter(patterns=["**/graphql-inputs.ts"])
        super().__init__(file_filter=file_filter)

    def _extract_from_file(self, file_data: dict[str, Any], file_path: str):
        input_types = []

        # Extract type aliases ending with Input
        for type_alias in file_data.get("typeAliases", []):
            name = type_alias.get("name", "")
            if name.endswith("Input"):
                # Parse the type definition
                type_def = type_alias.get("type", {})
                fields = []

                # Extract fields from object type
                if isinstance(type_def, dict) and type_def.get("type") == "object":
                    for prop in type_def.get("properties", []):
                        field = {
                            "name": prop.get("name", ""),
                            "type": prop.get("type", "String"),
                            "is_optional": prop.get("optional", False),
                            "description": prop.get("comment", ""),
                        }
                        fields.append(field)

                input_types.append(
                    {"name": name, "fields": fields, "description": type_alias.get("comment", "")}
                )

        # Also look in types array for types ending with Input
        for type_def in file_data.get("types", []):
            if isinstance(type_def, dict):
                name = type_def.get("name", "")
                if name.endswith("Input"):
                    # Parse the type string to extract fields
                    type_str = type_def.get("type", "")
                    fields = self._parse_input_type_string(type_str)

                    if fields:  # Only add if we found fields
                        input_types.append({"name": name, "fields": fields, "description": ""})

        return input_types

    def _parse_input_type_string(self, type_str: str) -> list[dict[str, Any]]:
        """Parse object type string like '{ x: Float; y: Float; }' into fields.

        Args:
            type_str: Type string to parse

        Returns:
            List of field dictionaries
        """
        fields = []

        # Simple parser for object type string
        if "{" in type_str and "}" in type_str:
            # Remove braces and split by semicolon
            content = type_str.strip().strip("{}").strip()
            if content:
                field_lines = content.split(";")
                for line in field_lines:
                    line = line.strip()
                    if ":" in line:
                        parts = line.split(":", 1)
                        field_name = parts[0].strip()
                        field_type = parts[1].strip() if len(parts) > 1 else "Any"

                        # Simplify Scalars['Type']['input'] to Type
                        if "Scalars[" in field_type:
                            match = re.search(r"Scalars\['(\w+)'\]", field_type)
                            if match:
                                field_type = match.group(1)

                        # Check if optional
                        is_optional = "?" in field_name or "InputMaybe<" in field_type
                        field_name = field_name.rstrip("?")

                        fields.append(
                            {
                                "name": field_name,
                                "type": field_type,
                                "is_optional": is_optional,
                                "description": "",
                            }
                        )

        return fields