"""Type Registry for Runtime Type Management.

This module provides a registry for managing custom types, branded types,
and enum types at runtime, allowing for dynamic type registration and lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class TypeInfo:
    """Information about a registered type."""

    name: str
    category: str  # 'branded', 'enum', 'custom', 'domain'
    python_type: str
    graphql_type: Optional[str] = None
    strawberry_type: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    converter: Optional[Callable[[Any], Any]] = None


class TypeRegistry:
    """Registry for managing custom types at runtime."""

    def __init__(self):
        """Initialize the type registry."""
        self._types: dict[str, TypeInfo] = {}
        self._branded_types: set[str] = set()
        self._enum_types: set[str] = set()
        self._custom_types: dict[str, str] = {}  # name -> python_type

    def register_type(
        self,
        name: str,
        category: str,
        python_type: str,
        graphql_type: Optional[str] = None,
        strawberry_type: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        converter: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """Register a custom type in the registry.

        Args:
            name: Type name
            category: Type category ('branded', 'enum', 'custom', 'domain')
            python_type: Python type string
            graphql_type: Optional GraphQL type string
            strawberry_type: Optional Strawberry type string
            metadata: Optional metadata dictionary
            converter: Optional conversion function
        """
        type_info = TypeInfo(
            name=name,
            category=category,
            python_type=python_type,
            graphql_type=graphql_type,
            strawberry_type=strawberry_type,
            metadata=metadata or {},
            converter=converter,
        )

        self._types[name] = type_info

        # Update category-specific registries
        if category == "branded":
            self._branded_types.add(name)
        elif category == "enum":
            self._enum_types.add(name)
        elif category == "custom":
            self._custom_types[name] = python_type

        logger.debug(f"Registered type: {name} ({category}) -> {python_type}")

    def register_branded_type(
        self,
        name: str,
        python_type: str = "str",
        graphql_type: Optional[str] = None,
        strawberry_type: Optional[str] = None,
    ) -> None:
        """Register a branded ID type.

        Args:
            name: Branded type name (e.g., 'NodeID', 'DiagramID')
            python_type: Python type to use (default: 'str')
            graphql_type: Optional GraphQL scalar name
            strawberry_type: Optional Strawberry scalar name
        """
        # Auto-generate GraphQL and Strawberry types if not provided
        if not graphql_type:
            graphql_type = name
        if not strawberry_type:
            strawberry_type = f"{name}Scalar"

        self.register_type(
            name=name,
            category="branded",
            python_type=python_type,
            graphql_type=graphql_type,
            strawberry_type=strawberry_type,
        )

    def register_enum_type(
        self,
        name: str,
        values: list[str],
        python_type: Optional[str] = None,
    ) -> None:
        """Register an enum type.

        Args:
            name: Enum type name
            values: List of enum values
            python_type: Optional Python enum class name (defaults to name)
        """
        python_type = python_type or name

        self.register_type(
            name=name,
            category="enum",
            python_type=python_type,
            graphql_type=name,
            strawberry_type=name,
            metadata={"values": values},
        )

    def register_custom_type(
        self,
        name: str,
        python_type: str,
        graphql_type: Optional[str] = None,
        strawberry_type: Optional[str] = None,
        converter: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """Register a custom type with optional conversion logic.

        Args:
            name: Type name
            python_type: Python type string
            graphql_type: Optional GraphQL type string
            strawberry_type: Optional Strawberry type string
            converter: Optional conversion function
        """
        self.register_type(
            name=name,
            category="custom",
            python_type=python_type,
            graphql_type=graphql_type,
            strawberry_type=strawberry_type,
            converter=converter,
        )

    def register_domain_type(
        self,
        name: str,
        fields: dict[str, str],
        graphql_type: Optional[str] = None,
        strawberry_type: Optional[str] = None,
    ) -> None:
        """Register a domain model type.

        Args:
            name: Domain type name (e.g., 'DomainNode', 'DomainDiagram')
            fields: Dictionary mapping field names to their types
            graphql_type: Optional GraphQL type name
            strawberry_type: Optional Strawberry type name
        """
        # Auto-generate GraphQL and Strawberry types if not provided
        if not graphql_type:
            graphql_type = name
        if not strawberry_type:
            strawberry_type = f"{name}Type"

        self.register_type(
            name=name,
            category="domain",
            python_type=name,
            graphql_type=graphql_type,
            strawberry_type=strawberry_type,
            metadata={"fields": fields},
        )

    def get_type_info(self, name: str) -> Optional[TypeInfo]:
        """Get type information by name.

        Args:
            name: Type name

        Returns:
            TypeInfo if found, None otherwise
        """
        return self._types.get(name)

    def get_python_type(self, name: str) -> Optional[str]:
        """Get Python type string for a registered type.

        Args:
            name: Type name

        Returns:
            Python type string if found, None otherwise
        """
        type_info = self._types.get(name)
        return type_info.python_type if type_info else None

    def get_graphql_type(self, name: str) -> Optional[str]:
        """Get GraphQL type string for a registered type.

        Args:
            name: Type name

        Returns:
            GraphQL type string if found, None otherwise
        """
        type_info = self._types.get(name)
        return type_info.graphql_type if type_info else None

    def get_strawberry_type(self, name: str) -> Optional[str]:
        """Get Strawberry type string for a registered type.

        Args:
            name: Type name

        Returns:
            Strawberry type string if found, None otherwise
        """
        type_info = self._types.get(name)
        return type_info.strawberry_type if type_info else None

    def is_branded_type(self, name: str) -> bool:
        """Check if a type is a branded ID type.

        Args:
            name: Type name

        Returns:
            True if type is branded, False otherwise
        """
        return name in self._branded_types

    def is_enum_type(self, name: str) -> bool:
        """Check if a type is an enum type.

        Args:
            name: Type name

        Returns:
            True if type is an enum, False otherwise
        """
        return name in self._enum_types

    def is_registered(self, name: str) -> bool:
        """Check if a type is registered.

        Args:
            name: Type name

        Returns:
            True if type is registered, False otherwise
        """
        return name in self._types

    def get_all_branded_types(self) -> set[str]:
        """Get all registered branded type names.

        Returns:
            Set of branded type names
        """
        return self._branded_types.copy()

    def get_all_enum_types(self) -> set[str]:
        """Get all registered enum type names.

        Returns:
            Set of enum type names
        """
        return self._enum_types.copy()

    def get_all_types(self) -> dict[str, TypeInfo]:
        """Get all registered types.

        Returns:
            Dictionary mapping type names to TypeInfo
        """
        return self._types.copy()

    def get_types_by_category(self, category: str) -> dict[str, TypeInfo]:
        """Get all types in a specific category.

        Args:
            category: Type category

        Returns:
            Dictionary of types in the category
        """
        return {name: info for name, info in self._types.items() if info.category == category}

    def convert_value(self, type_name: str, value: Any) -> Any:
        """Convert a value using the registered converter.

        Args:
            type_name: Type name
            value: Value to convert

        Returns:
            Converted value, or original value if no converter exists

        Raises:
            ValueError: If type is not registered
        """
        type_info = self._types.get(type_name)
        if not type_info:
            raise ValueError(f"Type not registered: {type_name}")

        if type_info.converter:
            return type_info.converter(value)

        return value

    def unregister_type(self, name: str) -> bool:
        """Unregister a type from the registry.

        Args:
            name: Type name

        Returns:
            True if type was unregistered, False if not found
        """
        if name not in self._types:
            return False

        type_info = self._types.pop(name)

        # Remove from category-specific registries
        if type_info.category == "branded":
            self._branded_types.discard(name)
        elif type_info.category == "enum":
            self._enum_types.discard(name)
        elif type_info.category == "custom":
            self._custom_types.pop(name, None)

        logger.debug(f"Unregistered type: {name}")
        return True

    def clear(self):
        """Clear all registered types."""
        self._types.clear()
        self._branded_types.clear()
        self._enum_types.clear()
        self._custom_types.clear()
        logger.debug("Type registry cleared")

    def load_from_config(self, config: dict[str, Any]):
        """Load types from a configuration dictionary.

        Args:
            config: Configuration dictionary with type definitions

        Example config structure:
            {
                "branded_types": ["NodeID", "DiagramID"],
                "enum_types": {
                    "Status": ["PENDING", "RUNNING", "COMPLETED"]
                },
                "custom_types": {
                    "CustomType": {
                        "python_type": "CustomClass",
                        "graphql_type": "CustomType"
                    }
                }
            }
        """
        # Load branded types
        for branded_type in config.get("branded_types", []):
            self.register_branded_type(branded_type)

        # Load enum types
        for enum_name, enum_values in config.get("enum_types", {}).items():
            self.register_enum_type(enum_name, enum_values)

        # Load custom types
        for type_name, type_config in config.get("custom_types", {}).items():
            self.register_custom_type(
                name=type_name,
                python_type=type_config.get("python_type", type_name),
                graphql_type=type_config.get("graphql_type"),
                strawberry_type=type_config.get("strawberry_type"),
            )

        logger.info(f"Loaded {len(self._types)} types from configuration")

    def export_to_config(self) -> dict[str, Any]:
        """Export all registered types to a configuration dictionary.

        Returns:
            Configuration dictionary
        """
        config = {
            "branded_types": list(self._branded_types),
            "enum_types": {},
            "custom_types": {},
            "domain_types": {},
        }

        for name, info in self._types.items():
            if info.category == "enum":
                config["enum_types"][name] = info.metadata.get("values", [])
            elif info.category == "custom":
                config["custom_types"][name] = {
                    "python_type": info.python_type,
                    "graphql_type": info.graphql_type,
                    "strawberry_type": info.strawberry_type,
                }
            elif info.category == "domain":
                config["domain_types"][name] = {
                    "python_type": info.python_type,
                    "graphql_type": info.graphql_type,
                    "strawberry_type": info.strawberry_type,
                    "fields": info.metadata.get("fields", {}),
                }

        return config


# Global type registry instance
_global_registry: Optional[TypeRegistry] = None


def get_global_registry() -> TypeRegistry:
    """Get the global type registry instance.

    Returns:
        Global TypeRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = TypeRegistry()
    return _global_registry


def reset_global_registry():
    """Reset the global type registry (mainly for testing)."""
    global _global_registry
    _global_registry = None