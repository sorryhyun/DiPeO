"""Unified Type Converter for DiPeO Code Generation.

This module consolidates type conversion logic from:
1. TypeConverter (type_system/converter.py)
2. TypeConversionFilters (templates/filters/type_conversion_filters.py)

All type mappings are loaded from YAML configuration files, making the system
configuration-driven and easier to maintain.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import inflection
import yaml

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class UnifiedTypeConverter:
    """Unified type converter with configuration-driven mappings."""

    def __init__(
        self,
        config_dir: Path | None = None,
        custom_mappings: dict[str, dict[str, str]] | None = None,
    ):
        """Initialize the unified type converter.

        Args:
            config_dir: Directory containing YAML configuration files
            custom_mappings: Additional custom type mappings to override config
        """
        self.config_dir = config_dir or Path(__file__).parent
        self.custom_mappings = custom_mappings or {}

        # Load configuration from YAML files
        self.type_config = self._load_config("type_mappings.yaml")
        self.graphql_config = self._load_config("graphql_mappings.yaml")

        # Extract commonly used mappings for performance
        self._ts_to_py = self.type_config["base_types"]["typescript_to_python"]
        self._ts_to_gql = self.type_config["base_types"]["typescript_to_graphql"]
        self._gql_to_ts = self.type_config["base_types"]["graphql_to_typescript"]

        self._type_aliases = self.type_config["type_aliases"]
        self._branded_types = set(self.type_config["branded_types"])
        self._integer_fields = set(self.type_config["field_overrides"]["integer_fields"])
        self._context_fields = self.type_config["field_overrides"]["context_aware_fields"]

        # Type conversion cache for performance
        self._type_cache: dict[str, str] = {}

    def _load_config(self, filename: str) -> dict[str, Any]:
        """Load YAML configuration file.

        Args:
            filename: Name of the configuration file

        Returns:
            Parsed configuration dictionary
        """
        config_path = self.config_dir / filename
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}

        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    # ============================================================================
    # CASE CONVERSION UTILITIES
    # ============================================================================

    @staticmethod
    def snake_case(text: str) -> str:
        """Convert text to snake_case."""
        if not text or text == "Undefined":
            return ""
        return inflection.underscore(str(text))

    @staticmethod
    def camel_case(text: str) -> str:
        """Convert text to camelCase."""
        if not text or text == "Undefined":
            return ""
        return inflection.camelize(str(text), uppercase_first_letter=False)

    @staticmethod
    def pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        if not text or text == "Undefined":
            return ""
        return inflection.camelize(str(text))

    @staticmethod
    def kebab_case(text: str) -> str:
        """Convert text to kebab-case."""
        if not text or text == "Undefined":
            return ""
        return inflection.dasherize(inflection.underscore(str(text)))

    # ============================================================================
    # TYPESCRIPT → PYTHON CONVERSION
    # ============================================================================

    def ts_to_python(self, ts_type: str, field_name: str = "") -> str:
        """Convert TypeScript type to Python type.

        Args:
            ts_type: TypeScript type string
            field_name: Optional field name for context-specific conversions

        Returns:
            Python type string
        """
        if not ts_type:
            return "Any"

        # Check cache first
        cache_key = f"ts_py:{ts_type}:{field_name}"
        if cache_key in self._type_cache:
            return self._type_cache[cache_key]

        # Strip inline comments
        ts_type = self._strip_inline_comments(ts_type).strip()

        # Check custom mappings
        if (
            "ts_to_python" in self.custom_mappings
            and ts_type in self.custom_mappings["ts_to_python"]
        ):
            result = self.custom_mappings["ts_to_python"][ts_type]
            self._type_cache[cache_key] = result
            return result

        # Check type aliases
        if ts_type in self._type_aliases:
            result = self._type_aliases[ts_type]
            self._type_cache[cache_key] = result
            return result

        # Handle branded scalars
        branded = self._try_branded_scalar(ts_type)
        if branded:
            self._type_cache[cache_key] = branded
            return branded

        # Handle literal values
        if ts_type == "true":
            result = "Literal[True]"
            self._type_cache[cache_key] = result
            return result
        if ts_type == "false":
            result = "Literal[False]"
            self._type_cache[cache_key] = result
            return result

        # Handle inline object types
        if ts_type.startswith("{") and ts_type.endswith("}"):
            result = self._handle_inline_object(ts_type)
            self._type_cache[cache_key] = result
            return result

        # Handle union types (A | B | C)
        if "|" in ts_type:
            result = self._handle_union_type(ts_type, self.ts_to_python, field_name)
            self._type_cache[cache_key] = result
            return result

        # Handle string literals
        if self._is_string_literal(ts_type):
            result = f"Literal[{ts_type}]"
            self._type_cache[cache_key] = result
            return result

        # Handle array syntax (T[])
        if ts_type.endswith("[]"):
            inner_type = ts_type[:-2]
            result = f"List[{self.ts_to_python(inner_type, field_name)}]"
            self._type_cache[cache_key] = result
            return result

        # Handle tuple syntax [A, B, C]
        if ts_type.startswith("[") and ts_type.endswith("]"):
            elements = [
                self.ts_to_python(elem.strip(), field_name)
                for elem in ts_type[1:-1].split(",")
                if elem.strip()
            ]
            result = f"tuple[{', '.join(elements)}]" if elements else "tuple[]"
            self._type_cache[cache_key] = result
            return result

        # Handle generic syntax Foo<Bar>
        if "<" in ts_type and ts_type.endswith(">"):
            result = self._handle_generic_type(ts_type, field_name)
            self._type_cache[cache_key] = result
            return result

        # Base type mapping
        result = self._ts_to_py.get(ts_type, ts_type)

        # Apply field-specific overrides
        if result == "float" and field_name in self._integer_fields:
            result = "int"

        self._type_cache[cache_key] = result
        return result

    def _handle_generic_type(self, ts_type: str, field_name: str) -> str:
        """Handle generic TypeScript types like Array<T>, Record<K,V>, Promise<T>."""
        base, inner = ts_type.split("<", 1)
        inner = inner[:-1].strip()  # Remove trailing '>'
        base = base.strip()

        # Get conversion rule from config
        generic_rules = self.type_config["conversion_rules"]["generics"]

        if base == "Array":
            return f"List[{self.ts_to_python(inner, field_name)}]"
        elif base == "ReadonlyArray":
            return f"Sequence[{self.ts_to_python(inner, field_name)}]"
        elif base == "Promise":
            return f"Awaitable[{self.ts_to_python(inner, field_name)}]"
        elif base == "Record" or base == "Map":
            parts = inner.split(",", 1)
            if len(parts) == 2:
                key_type = self.ts_to_python(parts[0].strip(), field_name)
                value_type = self.ts_to_python(parts[1].strip(), field_name)
                if key_type == "float":
                    key_type = "int"
                return f"Dict[{key_type}, {value_type}]"
        elif base == "Partial":
            return f"Partial[{self.ts_to_python(inner, field_name)}]"
        elif base == "Required":
            return f"Required[{self.ts_to_python(inner, field_name)}]"

        # Generic case: convert inner types
        converted_inner = ", ".join(
            self.ts_to_python(part.strip(), field_name) for part in self._split_generic_args(inner)
        )
        return f"{base}[{converted_inner}]"

    def _handle_union_type(self, ts_type: str, converter_func, field_name: str = "") -> str:
        """Handle union types (A | B | C)."""
        parts = [part.strip() for part in ts_type.split("|")]

        # Separate null/undefined from other types
        has_null = "null" in parts or "undefined" in parts
        non_null_parts = [part for part in parts if part not in {"null", "undefined"}]

        # If we have null/undefined and only one other type, make it Optional
        if has_null and len(non_null_parts) == 1:
            other_type = non_null_parts[0]
            return f"Optional[{converter_func(other_type, field_name)}]"

        # If we have null/undefined and multiple other types, make the union Optional
        if has_null and len(non_null_parts) > 1:
            # Check if all non-null parts are literals
            all_literals = all(self._is_string_literal(part) for part in non_null_parts)
            if all_literals:
                literal_values = ", ".join(non_null_parts)
                return f"Optional[Literal[{literal_values}]]"

            # Build union and wrap in Optional
            converted_parts = []
            for part in non_null_parts:
                if self._is_string_literal(part):
                    converted_parts.append(f"Literal[{part}]")
                else:
                    converted_parts.append(converter_func(part, field_name))

            if len(converted_parts) == 1:
                return f"Optional[{converted_parts[0]}]"
            return f'Optional[Union[{", ".join(converted_parts)}]]'

        # No null/undefined - check if all parts are literals
        all_literals = all(self._is_string_literal(part) for part in parts)
        if all_literals:
            literal_values = ", ".join(parts)
            return f"Literal[{literal_values}]"

        # General union handling (no null/undefined)
        converted_parts = []
        for part in parts:
            if self._is_string_literal(part):
                converted_parts.append(f"Literal[{part}]")
            else:
                converted_parts.append(converter_func(part, field_name))

        if not converted_parts:
            return "None"
        if len(converted_parts) == 1:
            return converted_parts[0]

        return f'Union[{", ".join(converted_parts)}]'

    def _handle_inline_object(self, ts_type: str) -> str:
        """Handle inline object types like { [key: string]: Foo }."""
        # Index signature { [key: string]: Foo }
        if re.search(r"\[\s*\w+\s*:\s*\w+\s*\]\s*:\s*\w+", ts_type):
            match = re.search(r"\[\s*\w+\s*:\s*(\w+)\s*\]\s*:\s*(\w+)", ts_type)
            if match:
                key_type = self.ts_to_python(match.group(1))
                value_type = self.ts_to_python(match.group(2))
                if key_type == "float":
                    key_type = "int"
                return f"Dict[{key_type}, {value_type}]"
        return "Dict[str, Any]"

    def _try_branded_scalar(self, ts_type: str) -> str | None:
        """Try to extract branded scalar type."""
        # Check if it's a known branded type
        if ts_type in self._branded_types:
            return ts_type

        # Check if it matches branded pattern
        if "&" in ts_type and "__brand" in ts_type:
            branded_pattern = self.type_config["patterns"]["branded_pattern"]
            match = re.search(branded_pattern, ts_type)
            if match:
                brand = match.group(1)
                return brand if brand.endswith("ID") else brand

        return None

    def _is_string_literal(self, ts_type: str) -> bool:
        """Check if type is a string literal."""
        ts_type = ts_type.strip()
        return (ts_type.startswith("'") and ts_type.endswith("'")) or (
            ts_type.startswith('"') and ts_type.endswith('"')
        )

    def _split_generic_args(self, inner: str) -> list[str]:
        """Split generic arguments handling nested generics."""
        depth = 0
        current = []
        parts: list[str] = []
        for char in inner:
            if char == "<":
                depth += 1
            elif char == ">":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append("".join(current))
                current = []
                continue
            current.append(char)
        if current:
            parts.append("".join(current))
        return parts

    # ============================================================================
    # TYPESCRIPT → GRAPHQL CONVERSION
    # ============================================================================

    def ts_to_graphql(self, ts_type: str) -> str:
        """Convert TypeScript type to GraphQL type.

        Args:
            ts_type: TypeScript type string

        Returns:
            GraphQL type string
        """
        if not ts_type:
            return "JSONScalar"

        ts_type = ts_type.strip()

        # Check custom mappings
        if (
            "ts_to_graphql" in self.custom_mappings
            and ts_type in self.custom_mappings["ts_to_graphql"]
        ):
            return self.custom_mappings["ts_to_graphql"][ts_type]

        # Handle arrays
        if ts_type.endswith("[]"):
            inner = ts_type[:-2]
            return f"[{self.ts_to_graphql(inner)}]"

        if ts_type.startswith("Array<") and ts_type.endswith(">"):
            inner = ts_type[6:-1]
            return f"[{self.ts_to_graphql(inner)}]"

        # Handle branded scalars
        branded = self._try_branded_scalar(ts_type)
        if branded:
            return branded

        return self._ts_to_gql.get(ts_type, ts_type)

    # ============================================================================
    # GRAPHQL CONVERSIONS
    # ============================================================================

    def graphql_to_ts(self, graphql_type: str) -> str:
        """Convert GraphQL type to TypeScript type.

        Args:
            graphql_type: GraphQL type string

        Returns:
            TypeScript type string
        """
        if not graphql_type:
            return "any"

        # Check custom mappings
        if (
            "graphql_to_ts" in self.custom_mappings
            and graphql_type in self.custom_mappings["graphql_to_ts"]
        ):
            return self.custom_mappings["graphql_to_ts"][graphql_type]

        # Handle arrays [T]
        if graphql_type.startswith("[") and graphql_type.endswith("]"):
            inner = graphql_type[1:-1].replace("!", "")
            return f"{self.graphql_to_ts(inner)}[]"

        clean_type = graphql_type.replace("!", "")
        return self._gql_to_ts.get(clean_type, clean_type)

    def graphql_to_python(self, graphql_type: str, required: bool = True) -> str:
        """Convert GraphQL type to Python type.

        Args:
            graphql_type: GraphQL type string
            required: Whether the field is required

        Returns:
            Python type string
        """
        ts_type = self.graphql_to_ts(graphql_type)
        python_type = self.ts_to_python(ts_type)

        # Maintain lowercase list typing for backwards compatibility
        if python_type.startswith("List["):
            python_type = "list" + python_type[4:]

        if not required and not graphql_type.endswith("!"):
            if not python_type.startswith("Optional["):
                python_type = f"Optional[{python_type}]"

        return python_type

    # ============================================================================
    # GRAPHQL INPUT CONVERSIONS (for GraphQL codegen)
    # ============================================================================

    def ts_graphql_input_to_python(self, ts_type: str, field_name: str = "") -> str:
        """Convert TypeScript GraphQL input syntax to Python type.

        Handles special GraphQL input patterns:
        - Scalars['Type']['input'] → Python type
        - InputMaybe<T> → Optional[T]
        - Array<T> → List[T]

        Args:
            ts_type: TypeScript GraphQL input type string
            field_name: Optional field name for context

        Returns:
            Python type string
        """
        if not ts_type:
            return "JSON"  # Default to JSON for GraphQL

        ts_type = ts_type.strip()

        # Handle Scalars['Type']['input'] pattern
        scalars_match = re.match(r"Scalars\['(\w+)'\]\['input'\]", ts_type)
        if scalars_match:
            scalar_type = scalars_match.group(1)
            scalar_map = self.graphql_config["graphql_input_mappings"]["scalar_inputs"]
            return scalar_map.get(scalar_type, scalar_type)

        # Handle InputMaybe<T> pattern
        input_maybe_match = re.match(r"InputMaybe<(.+)>", ts_type, re.DOTALL)
        if input_maybe_match:
            inner_type = input_maybe_match.group(1).strip()
            python_type = self.ts_graphql_input_to_python(inner_type, field_name)
            if not python_type.startswith("Optional["):
                return f"Optional[{python_type}]"
            return python_type

        # Handle Array<T> pattern
        array_match = re.match(r"Array<(.+)>", ts_type, re.DOTALL)
        if array_match:
            inner_type = array_match.group(1).strip()
            python_type = self.ts_graphql_input_to_python(inner_type, field_name)
            return f"List[{python_type}]"

        # Handle Maybe<T> pattern
        maybe_match = re.match(r"Maybe<(.+)>", ts_type, re.DOTALL)
        if maybe_match:
            inner_type = maybe_match.group(1).strip()
            python_type = self.ts_graphql_input_to_python(inner_type, field_name)
            if not python_type.startswith("Optional["):
                return f"Optional[{python_type}]"
            return python_type

        # Handle input type references (e.g., Vec2Input)
        if ts_type.endswith("Input"):
            return ts_type

        # Handle branded ID types
        if ts_type in self._branded_types:
            return "str"

        # Check for JSON field patterns
        json_field_patterns = set(self.graphql_config["json_field_patterns"])
        if field_name in json_field_patterns or field_name.endswith("_data"):
            if ts_type in ["any", "Any", "unknown", "object", "{}", "Record<string, any>"]:
                return "JSON"

        # Handle primitive types
        primitive_map = {
            "string": "str",
            "number": "float",
            "boolean": "bool",
            "any": "JSON",
            "unknown": "JSON",
            "object": "JSON",
            "void": "None",
            "null": "None",
            "undefined": "None",
        }

        if ts_type in primitive_map:
            mapped = primitive_map[ts_type]
            if mapped == "float" and field_name in self._integer_fields:
                return "int"
            return mapped

        # Handle T[] array syntax
        if ts_type.endswith("[]"):
            inner_type = ts_type[:-2]
            python_type = self.ts_graphql_input_to_python(inner_type, field_name)
            return f"List[{python_type}]"

        # Handle Record<K, V> and Dict patterns
        if (
            ts_type.startswith("Record<")
            or ts_type.startswith("Dict")
            or ts_type.startswith("dict")
        ):
            return "JSON"

        # Default: return as-is (likely a type reference)
        return ts_type

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    @staticmethod
    def _strip_inline_comments(type_str: str) -> str:
        """Strip inline comments from type strings."""
        if "//" in type_str:
            type_str = type_str.split("//")[0].strip()
        if "/*" in type_str and "*/" in type_str:
            type_str = re.sub(r"/\*.*?\*/", "", type_str).strip()
        return type_str

    def ensure_optional(self, type_str: str) -> str:
        """Ensure a type is wrapped in Optional if not already."""
        if not type_str or type_str.startswith("Optional["):
            return type_str
        return f"Optional[{type_str}]"

    def is_optional_type(self, ts_type: str) -> bool:
        """Check if a TypeScript type is optional."""
        ts_type = ts_type.strip()
        return (
            ts_type.endswith(" | undefined")
            or ts_type.endswith(" | null")
            or "undefined" in ts_type.split("|")
            or "null" in ts_type.split("|")
        )

    def is_branded_type(self, type_name: str) -> bool:
        """Check if a type is a branded ID type."""
        return type_name in self._branded_types

    def get_default_value(self, py_type: str, is_optional: bool = False) -> str:
        """Get appropriate default value for a Python type.

        Args:
            py_type: Python type string
            is_optional: Whether the type is optional

        Returns:
            Default value string
        """
        if is_optional:
            return "None"

        # Check config for default values
        defaults = self.type_config["default_values"]

        # Check exact match first
        if py_type in defaults:
            return defaults[py_type]

        # Check pattern matches
        if py_type.startswith("List["):
            return defaults["List[*]"]
        elif py_type.startswith("Dict["):
            return defaults["Dict[*]"]
        elif py_type.startswith("Set["):
            return defaults["Set[*]"]
        elif py_type.startswith("Tuple["):
            return defaults["Tuple[*]"]
        elif py_type.startswith("Optional["):
            return defaults["Optional[*]"]

        return "None"

    def get_python_imports(self, types_used: list[str]) -> list[str]:
        """Generate Python import statements based on types used.

        Args:
            types_used: List of Python type strings

        Returns:
            List of import statements
        """
        imports = set()
        import_map = self.type_config["python_imports"]

        for type_str in types_used:
            for pattern, import_stmt in import_map.items():
                if pattern in type_str:
                    imports.add(import_stmt)

        return sorted(list(imports))

    def python_type_with_context(
        self,
        field: dict[str, Any],
        node_type: str,
        mappings: dict[str, Any] | None = None,
    ) -> str:
        """Convert field type to Python type with context awareness.

        Args:
            field: Field definition dictionary
            node_type: Type of the node containing the field
            mappings: Optional custom mappings

        Returns:
            Python type string
        """
        field_name = field.get("name", "")
        field_type = field.get("type", "string")
        is_required = field.get("required", False)

        # Check context-aware field mappings
        if field_name in self._context_fields:
            base_type = self._context_fields[field_name]
        elif mappings and "ts_to_py_type" in mappings and field_type in mappings["ts_to_py_type"]:
            base_type = str(mappings["ts_to_py_type"][field_type])
        # Special handling for person_job node
        elif node_type == "person_job":
            person_job_overrides = self.graphql_config.get("person_job_field_overrides", {})
            if field_name in person_job_overrides:
                base_type = person_job_overrides[field_name]
            else:
                base_type = self.ts_to_python(field_type, field_name)
        else:
            base_type = self.ts_to_python(field_type, field_name)

        # Handle optional
        if not is_required:
            if field_type in ["object", "dict", "array", "list"]:
                return f"Optional[{base_type}]"
            if "default" in field and field["default"] is not None:
                return base_type
            return f"Optional[{base_type}]"

        return base_type

    def clear_cache(self):
        """Clear the type conversion cache."""
        self._type_cache.clear()
