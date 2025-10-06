"""Unified Type Resolver for Strawberry GraphQL.

This module consolidates type resolution logic from StrawberryTypeResolver,
providing field resolution, type mapping, and conversion method generation
for Strawberry GraphQL schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.config.base_logger import get_module_logger

from .converter import UnifiedTypeConverter

logger = get_module_logger(__name__)


@dataclass
class ResolvedField:
    """Resolved field information for template rendering."""

    name: str
    python_type: str  # Python type for Pydantic model
    strawberry_type: str  # Strawberry GraphQL type
    default: str  # Default value expression (e.g., " = None", " = []")
    is_optional: bool
    is_json: bool
    is_literal: bool
    is_custom_list: bool
    needs_conversion: bool
    conversion_expr: str | None = None  # Expression for from_pydantic conversion


@dataclass
class ConversionMethod:
    """Generated conversion method for a type."""

    type_name: str
    method_code: str
    needs_method: bool


class TypeConversionRegistry:
    """Registry of reusable type conversion patterns."""

    @staticmethod
    def enum_value(field_name: str, source: str = "obj") -> str:
        """Convert enum to string value."""
        return f"str({source}.{field_name}.value) if hasattr({source}.{field_name}, 'value') else str({source}.{field_name})"

    @staticmethod
    def json_scalar(field_name: str, source: str = "obj") -> str:
        """Convert to JSON scalar."""
        return f"{source}.{field_name}"

    @staticmethod
    def nested_type(field_name: str, type_name: str, source: str = "obj") -> str:
        """Convert nested Pydantic type to Strawberry type."""
        return f"{type_name}.from_pydantic({source}.{field_name}) if hasattr({type_name}, 'from_pydantic') else {source}.{field_name}"

    @staticmethod
    def nested_list(field_name: str, item_type: str, source: str = "obj") -> str:
        """Convert list of Pydantic types to Strawberry types."""
        return f"[{item_type}.from_pydantic(item) for item in {source}.{field_name}] if {source}.{field_name} else []"

    @staticmethod
    def dict_to_json(field_name: str, source: str = "obj") -> str:
        """Convert dictionary to JSON-serializable format."""
        return f"""{{k: v.model_dump() if hasattr(v, 'model_dump') else v
                    for k, v in {source}.{field_name}.items()}} if {source}.{field_name} else {{}}"""

    @staticmethod
    def optional_nested(field_name: str, type_name: str, source: str = "obj") -> str:
        """Convert optional nested type."""
        return f"{type_name}.from_pydantic({source}.{field_name}) if {source}.{field_name} and hasattr({type_name}, 'from_pydantic') else {source}.{field_name}"


class UnifiedTypeResolver:
    """Unified type resolver for Strawberry GraphQL generation."""

    def __init__(
        self,
        config_path: Path | None = None,
        converter: UnifiedTypeConverter | None = None,
    ):
        """Initialize unified type resolver.

        Args:
            config_path: Path to configuration directory (defaults to module directory)
            converter: Optional UnifiedTypeConverter instance (creates new one if not provided)
        """
        self.config_dir = config_path or Path(__file__).parent
        self.converter = converter or UnifiedTypeConverter(config_dir=self.config_dir)

        # Load GraphQL-specific configuration
        self.graphql_config = self._load_config("graphql_mappings.yaml")

        # Extract commonly used mappings
        self.scalar_mappings = self.graphql_config.get("scalar_mappings", {})
        self.json_types = set(self.graphql_config.get("json_types", []))
        self.manual_conversion_types = set(self.graphql_config.get("manual_conversion_types", []))
        self.pydantic_decorator_types = set(self.graphql_config.get("pydantic_decorator_types", []))

        # Load type_suffix_types from config
        self.type_suffix_types = set(
            self.graphql_config.get("strawberry_type_rules", {}).get("type_suffix_types", [])
        )

        self.conversion_registry = TypeConversionRegistry()

    def _load_config(self, filename: str) -> dict[str, Any]:
        """Load YAML configuration file."""
        config_path = self.config_dir / filename
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}

        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    def resolve_field(self, field: dict[str, Any], type_name: str) -> ResolvedField:
        """Resolve all field type information for template rendering.

        Args:
            field: Field definition from IR
            type_name: Name of the containing type

        Returns:
            ResolvedField with all resolved type information
        """
        field_name = field.get("name", "")
        field_type = field.get("type", "Any")
        is_optional = field.get("optional", False) or field.get("isOptional", False)

        # Special case for envelope_format field which has literal value "true"
        if field_name == "envelope_format" and field_type == "true":
            return ResolvedField(
                name=field_name,
                python_type="bool",
                strawberry_type="bool",
                default=" = True",
                is_optional=False,
                is_json=False,
                is_literal=False,
                is_custom_list=False,
                needs_conversion=False,
                conversion_expr=None,
            )

        # Check for special field types
        is_json = self._is_json_field(field_type)
        is_literal = self._is_literal_field(field_type)
        is_custom_list = self._is_custom_list(field_type)

        # Resolve Strawberry type
        strawberry_type = self._resolve_strawberry_type(
            field_name, field_type, is_optional, type_name
        )

        # Determine default value
        default = self._get_default_value(strawberry_type, is_optional)

        # Check if field needs conversion in from_pydantic
        needs_conversion = self._needs_conversion(field_name, field_type, type_name)

        # Generate conversion expression if needed
        conversion_expr = None
        if needs_conversion:
            conversion_expr = self._generate_conversion_expr(field_name, field_type, type_name)

        return ResolvedField(
            name=field_name,
            python_type=field_type,
            strawberry_type=strawberry_type,
            default=default,
            is_optional=is_optional,
            is_json=is_json,
            is_literal=is_literal,
            is_custom_list=is_custom_list,
            needs_conversion=needs_conversion,
            conversion_expr=conversion_expr,
        )

    def _is_json_field(self, field_type: str) -> bool:
        """Check if field should be rendered as JSON scalar."""
        return any(json_type in field_type for json_type in self.json_types)

    def _is_literal_field(self, field_type: str) -> bool:
        """Check if field is a literal type."""
        return (
            field_type.startswith("'")
            or field_type.startswith('"')
            or "Literal[" in field_type
            or "Union['" in field_type
        )

    def _is_custom_list(self, field_type: str) -> bool:
        """Check if field is a list of custom domain types."""
        return (
            field_type.startswith("List[Domain")
            or field_type.startswith("list[Domain")
            or field_type.startswith("List[Message")
            or field_type.startswith("list[Message")
        )

    def _resolve_strawberry_type(
        self, field_name: str, field_type: str, is_optional: bool, type_name: str
    ) -> str:
        """Resolve the Strawberry GraphQL type for a field."""
        # Handle ID scalars
        if field_name == "id":
            # Map to appropriate scalar based on type name
            if type_name.startswith("Domain"):
                entity = type_name[6:]  # Remove "Domain" prefix
                scalar_key = f"{entity}ID"
                base_type = self.scalar_mappings.get(scalar_key, "str")
            else:
                # Try to find matching scalar
                scalar_key = f"{type_name.replace('Type', '')}ID"
                base_type = self.scalar_mappings.get(scalar_key, "str")

        # Handle branded ID types
        elif field_type in self.scalar_mappings:
            base_type = self.scalar_mappings[field_type]

        # Handle Dict types - check before JSON fields
        elif field_type.startswith("Dict[") or field_type.startswith("dict["):
            base_type = self._resolve_dict_type(field_type)

        # Handle JSON fields
        elif self._is_json_field(field_type):
            base_type = "JSONScalar"

        # Handle literal fields
        elif self._is_literal_field(field_type):
            base_type = "str"

        # Handle list types
        elif field_type.startswith("List[") or field_type.startswith("list["):
            base_type = self._resolve_list_type(field_type)

        # Handle domain types
        elif field_type.startswith("Domain"):
            base_type = f"{field_type}Type"

        # Handle Optional types first (extract inner type)
        elif field_type.startswith("Optional["):
            inner_type = field_type[9:-1]  # Extract type from Optional[...]
            # Recursively resolve the inner type
            base_type = self._resolve_strawberry_type(field_name, inner_type, False, type_name)
            is_optional = True  # Mark as optional for later processing

        # Handle known complex types that need Type suffix
        elif field_type in self.type_suffix_types:
            base_type = f"{field_type}Type"

        # Handle enums (these should be imported from enums module)
        elif field_type in self.graphql_config.get("strawberry_type_rules", {}).get(
            "enum_types", []
        ):
            base_type = field_type  # Keep enum name as-is

        # Handle Union types
        elif field_type.startswith("Union["):
            # For now, use JSONScalar
            base_type = "JSONScalar"

        # Handle literal true/false values
        elif field_type == "true" or field_type == "false":
            base_type = "bool"

        else:
            # Handle specific ID types
            if field_type == "DiagramID":
                base_type = "DiagramIDScalar"
            else:
                # Default mapping
                type_map = {
                    "str": "str",
                    "int": "int",
                    "float": "float",
                    "bool": "bool",
                    "Any": "JSONScalar",
                    "SerializedNodeOutput": "JSONScalar",
                }
                base_type = type_map.get(field_type, field_type)

        # Add Optional wrapper if needed
        if is_optional and not base_type.startswith("Optional["):
            return f"Optional[{base_type}]"

        return base_type

    def _resolve_dict_type(self, field_type: str) -> str:
        """Resolve dictionary types to appropriate GraphQL type."""
        # Extract the dict content
        if field_type.startswith("Dict["):
            dict_content = field_type[5:-1]
        else:
            dict_content = field_type[5:-1]  # dict[

        # Split by comma to get key and value types
        parts = dict_content.split(",", 1)
        if len(parts) == 2:
            value_type = parts[1].strip()

            # Check if value type should be JSONScalar
            dict_config = self.graphql_config.get("dict_value_to_graphql", {})
            json_scalar_values = dict_config.get("json_scalar_values", [])

            should_use_json = (
                value_type in json_scalar_values
                or value_type.startswith("Domain")
                or value_type in self.manual_conversion_types
                or self._is_json_field(field_type)
                or value_type in ["float", "int", "bool", "Any"]
            )

            if should_use_json:
                return "JSONScalar"
            else:
                # Only simple Dict[str, str] can be used directly
                return field_type  # Keep Dict with uppercase D

        return "JSONScalar"

    def _resolve_list_type(self, field_type: str) -> str:
        """Resolve list types to appropriate GraphQL type."""
        inner_type = field_type[5:-1] if field_type.startswith("List[") else field_type[5:-1]

        # Handle list of domain types
        if inner_type.startswith("Domain"):
            return f"List[{inner_type}Type]"
        # Check if inner type needs Type suffix
        elif inner_type in self.type_suffix_types:
            return f"List[{inner_type}Type]"
        else:
            return f"List[{inner_type}]"

    def _get_default_value(self, strawberry_type: str, is_optional: bool) -> str:
        """Get the default value expression for a field."""
        if is_optional or strawberry_type.startswith("Optional["):
            return " = None"

        # No default for required fields
        return ""

    def _needs_conversion(self, field_name: str, field_type: str, type_name: str) -> bool:
        """Check if field needs conversion in from_pydantic method."""
        # Check if type needs manual conversion
        if type_name in self.manual_conversion_types:
            # These fields typically need conversion
            if field_name in ["type", "status", "content_type"]:
                return True
            if self._is_custom_list(field_type):
                return True
            if field_type.startswith("Domain"):
                return True
            if field_name in ["node_states", "node_outputs", "exec_counts"]:
                return True

        return False

    def _generate_conversion_expr(self, field_name: str, field_type: str, type_name: str) -> str:
        """Generate conversion expression for from_pydantic method."""
        # Check conversion templates from config
        templates = self.graphql_config.get("conversion_templates", {})

        # Enum conversion
        if field_name in ["type", "status", "content_type"]:
            return self.conversion_registry.enum_value(field_name)

        # List of domain types
        if field_type.startswith("List[Domain") or field_type.startswith("list[Domain"):
            item_type = field_type[5:-1] + "Type"  # DomainNode -> DomainNodeType
            return self.conversion_registry.nested_list(field_name, item_type)

        # Domain types
        if field_type.startswith("Domain"):
            return self.conversion_registry.nested_type(field_name, f"{field_type}Type")

        # Dict to JSON
        if field_name in ["node_states", "node_outputs"]:
            return self.conversion_registry.dict_to_json(field_name)

        # Default: use field directly
        return f"obj.{field_name}"

    def generate_conversion_method(
        self, type_name: str, fields: list[ResolvedField]
    ) -> ConversionMethod:
        """Generate from_pydantic conversion method for a type."""
        # Check if type needs manual conversion
        needs_conversion = type_name in self.manual_conversion_types or any(
            f.needs_conversion for f in fields
        )

        if not needs_conversion:
            return ConversionMethod(type_name=type_name, method_code="", needs_method=False)

        # Generate method code
        lines = [
            "@staticmethod",
            f'def from_pydantic(obj: {type_name}) -> "{type_name}Type":',
            '    """Convert from Pydantic model"""',
        ]

        # Add any pre-conversion logic (special cases)
        if type_name == "DomainNode":
            lines.append("    # Convert position")
            lines.append(
                "    position = Vec2Type.from_pydantic(obj.position) if hasattr(Vec2Type, 'from_pydantic') else Vec2Type(x=obj.position.x, y=obj.position.y)"
            )
        elif type_name == "ExecutionState":
            lines.append("    # Convert nested types")
            lines.append(
                "    llm_usage = LLMUsageType.from_pydantic(obj.llm_usage) if hasattr(LLMUsageType, 'from_pydantic') else obj.llm_usage"
            )
            lines.append(
                "    metrics = ExecutionMetricsType.from_pydantic(obj.metrics) if obj.metrics and hasattr(ExecutionMetricsType, 'from_pydantic') else obj.metrics"
            )

        # Generate return statement
        lines.append(f"    return {type_name}Type(")

        for field in fields:
            if field.needs_conversion and field.conversion_expr:
                lines.append(f"        {field.name}={field.conversion_expr},")
            else:
                lines.append(f"        {field.name}=obj.{field.name},")

        lines.append("    )")

        return ConversionMethod(
            type_name=type_name, method_code="\n".join(lines), needs_method=True
        )

    def process_type(self, interface: dict[str, Any]) -> dict[str, Any]:
        """Process a complete type for template rendering.

        Args:
            interface: Interface/type definition from IR

        Returns:
            Processed type data ready for template
        """
        type_name = interface["name"]

        # Resolve all fields
        resolved_fields = [
            self.resolve_field(prop, type_name) for prop in interface.get("properties", [])
        ]

        # Generate conversion method if needed
        conversion_method = self.generate_conversion_method(type_name, resolved_fields)

        # Check if we can use all_fields decorator
        use_all_fields = not conversion_method.needs_method

        return {
            "name": type_name,
            "resolved_fields": resolved_fields,
            "needs_manual_conversion": conversion_method.needs_method,
            "conversion_method": conversion_method.method_code,
            "use_all_fields": use_all_fields,
            "description": interface.get("description", ""),
        }

    def should_use_pydantic_decorator(self, type_name: str) -> bool:
        """Check if a type can use @strawberry.experimental.pydantic.type decorator.

        Args:
            type_name: Name of the type

        Returns:
            True if type can use pydantic decorator, False otherwise
        """
        return type_name in self.pydantic_decorator_types

    def should_use_manual_conversion(self, type_name: str) -> bool:
        """Check if a type needs manual conversion logic.

        Args:
            type_name: Name of the type

        Returns:
            True if type needs manual conversion, False otherwise
        """
        return type_name in self.manual_conversion_types
