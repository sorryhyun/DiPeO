"""Shared type conversion utilities for the code generation pipeline."""

from __future__ import annotations

import re
from typing import Any, Optional

import inflection


# ============================================================================
# CASE CONVERSION UTILITIES
# ============================================================================


def snake_case(text: str) -> str:
    """Convert text to snake_case using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.underscore(str(text))


def camel_case(text: str) -> str:
    """Convert text to camelCase using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text), uppercase_first_letter=False)


def pascal_case(text: str) -> str:
    """Convert text to PascalCase using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.camelize(str(text))


def kebab_case(text: str) -> str:
    """Convert text to kebab-case using the inflection library."""
    if not text or text == "Undefined":
        return ""
    return inflection.dasherize(inflection.underscore(str(text)))


# Aliases for backward compatibility
camel_to_snake = snake_case
snake_to_pascal = pascal_case
pascal_to_camel = camel_case


# ============================================================================
# TYPE CONVERSION UTILITIES
# ============================================================================


class TypeConverter:
    """Unified type converter for TypeScript, Python, and GraphQL types."""

    TS_TO_PYTHON_BASE = {
        "string": "str",
        "number": "float",
        "boolean": "bool",
        "any": "Any",
        "unknown": "Any",
        "null": "None",
        "undefined": "None",
        "void": "None",
        "Date": "datetime",
        "Object": "Dict[str, Any]",
        "object": "Dict[str, Any]",
        "Record<string, any>": "Dict[str, Any]",
        "Record<string, string>": "Dict[str, str]",
    }

    TS_TO_GRAPHQL = {
        "string": "String",
        "number": "Float",
        "boolean": "Boolean",
        "any": "JSONScalar",
        "unknown": "JSONScalar",
        "Date": "DateTime",
        "Record<string, any>": "JSONScalar",
        "Record<string, string>": "JSONScalar",
        "object": "JSONScalar",
        "Object": "JSONScalar",
    }

    GRAPHQL_TO_TS = {
        "String": "string",
        "Int": "number",
        "Float": "number",
        "Boolean": "boolean",
        "ID": "string",
        "DateTime": "string",
        "JSON": "any",
        "JSONScalar": "any",
        "Upload": "Upload",
    }

    def __init__(self, custom_mappings: Optional[dict[str, dict[str, str]]] = None):
        self.custom_mappings = custom_mappings or {}

    # ------------------------------------------------------------------
    # TypeScript → Python
    # ------------------------------------------------------------------

    def ts_to_python(self, ts_type: str) -> str:
        """Convert a TypeScript type string into a Python type."""
        if not ts_type:
            return "Any"

        ts_type = ts_type.strip()

        # Custom mappings first
        if "ts_to_python" in self.custom_mappings:
            mapping = self.custom_mappings["ts_to_python"]
            if ts_type in mapping:
                return mapping[ts_type]

        # Historical aliases used throughout the codebase
        if ts_type == "SerializedNodeOutput":
            return "SerializedEnvelope"
        if ts_type == "PersonMemoryMessage":
            return "Message"

        # Handle branded scalars before mutating the string
        branded = self._try_branded_scalar(ts_type)
        if branded is not None:
            return branded

        # Handle union types (A | B | C)
        if "|" in ts_type:
            return self._handle_union_type(ts_type, self.ts_to_python)

        # Handle literal strings
        if self._is_string_literal(ts_type):
            return f"Literal[{ts_type}]"

        # Handle array syntax (T[])
        if ts_type.endswith("[]"):
            inner_type = ts_type[:-2]
            return f"List[{self.ts_to_python(inner_type)}]"

        # Handle tuple syntax [A, B]
        if ts_type.startswith("[") and ts_type.endswith("]"):
            elements = [self.ts_to_python(elem.strip()) for elem in ts_type[1:-1].split(",") if elem.strip()]
            return f"tuple[{', '.join(elements)}]" if elements else "tuple[]"

        # Handle generic syntax Foo<Bar>
        if "<" in ts_type and ts_type.endswith(">"):
            base, inner = ts_type.split("<", 1)
            inner = inner[:-1]  # strip trailing '>'
            base = base.strip()

            if base == "Array":
                return f"List[{self.ts_to_python(inner)}]"
            if base == "ReadonlyArray":
                return f"Sequence[{self.ts_to_python(inner)}]"
            if base == "Promise":
                return f"Awaitable[{self.ts_to_python(inner)}]"
            if base == "Record":
                parts = inner.split(",", 1)
                if len(parts) == 2:
                    key_type = self.ts_to_python(parts[0].strip())
                    value_type = self.ts_to_python(parts[1].strip())
                    if key_type == "float":
                        key_type = "int"
                    return f"Dict[{key_type}, {value_type}]"
            if base == "Partial":
                return f"Partial[{self.ts_to_python(inner)}]"
            if base == "Required":
                return f"Required[{self.ts_to_python(inner)}]"

            converted_inner = ", ".join(self.ts_to_python(part.strip()) for part in self._split_generic_args(inner))
            return f"{base}[{converted_inner}]"

        # Handle Record<K,V> and other inline object signatures
        if ts_type.startswith("Record<") and ts_type.endswith(">"):
            inner = ts_type[7:-1]
            parts = inner.split(",", 1)
            if len(parts) == 2:
                key_type = self.ts_to_python(parts[0].strip())
                value_type = self.ts_to_python(parts[1].strip())
                if key_type == "float":
                    key_type = "int"
                return f"Dict[{key_type}, {value_type}]"

        if ts_type.strip().startswith("{") and ts_type.strip().endswith("}"):
            # Inline object type
            if re.search(r"\[\s*\w+\s*:\s*\w+\s*\]\s*:\s*\w+", ts_type):
                # Index signature { [key: string]: Foo }
                match = re.search(r"\[\s*\w+\s*:\s*(\w+)\s*\]\s*:\s*(\w+)", ts_type)
                if match:
                    key_type = self.ts_to_python(match.group(1))
                    value_type = self.ts_to_python(match.group(2))
                    if key_type == "float":
                        key_type = "int"
                    return f"Dict[{key_type}, {value_type}]"
            return "Dict[str, Any]"

        # Base fallback mapping
        return self.TS_TO_PYTHON_BASE.get(ts_type, ts_type)

    # ------------------------------------------------------------------
    # TypeScript → GraphQL
    # ------------------------------------------------------------------

    def ts_to_graphql(self, ts_type: str) -> str:
        if not ts_type:
            return "JSONScalar"

        ts_type = ts_type.strip()

        if "ts_to_graphql" in self.custom_mappings:
            mapping = self.custom_mappings["ts_to_graphql"]
            if ts_type in mapping:
                return mapping[ts_type]

        if ts_type.endswith("[]"):
            inner = ts_type[:-2]
            return f"[{self.ts_to_graphql(inner)}]"

        if ts_type.startswith("Array<") and ts_type.endswith(">"):
            inner = ts_type[6:-1]
            return f"[{self.ts_to_graphql(inner)}]"

        branded = self._try_branded_scalar(ts_type)
        if branded is not None:
            return branded

        return self.TS_TO_GRAPHQL.get(ts_type, ts_type)

    # ------------------------------------------------------------------
    # GraphQL helpers
    # ------------------------------------------------------------------

    def graphql_to_ts(self, graphql_type: str) -> str:
        if not graphql_type:
            return "any"

        if "graphql_to_ts" in self.custom_mappings:
            mapping = self.custom_mappings["graphql_to_ts"]
            if graphql_type in mapping:
                return mapping[graphql_type]

        if graphql_type.startswith("[") and graphql_type.endswith("]"):
            inner = graphql_type[1:-1].replace("!", "")
            return f"{self.graphql_to_ts(inner)}[]"

        clean_type = graphql_type.replace("!", "")
        return self.GRAPHQL_TO_TS.get(clean_type, clean_type)

    def graphql_to_python(self, graphql_type: str) -> str:
        ts_type = self.graphql_to_ts(graphql_type)
        return self.ts_to_python(ts_type)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_string_literal(self, ts_type: str) -> bool:
        ts_type = ts_type.strip()
        return (ts_type.startswith("'") and ts_type.endswith("'")) or (
            ts_type.startswith('"') and ts_type.endswith('"')
        )

    def _handle_union_type(self, ts_type: str, converter_func) -> str:
        parts = [part.strip() for part in ts_type.split("|")]

        # Optional union Type | null/undefined
        if len(parts) == 2 and ("null" in parts or "undefined" in parts):
            other_type = parts[0] if parts[1] in {"null", "undefined"} else parts[1]
            return f"Optional[{converter_func(other_type)}]"

        all_literals = all(self._is_string_literal(part) for part in parts)
        if all_literals:
            literal_values = ", ".join(parts)
            return f"Literal[{literal_values}]"

        converted_parts = []
        for part in parts:
            if part in {"null", "undefined"}:
                continue
            if self._is_string_literal(part):
                converted_parts.append(f"Literal[{part}]")
            else:
                converted_parts.append(converter_func(part))

        if not converted_parts:
            return "None"
        if len(converted_parts) == 1:
            return f"Optional[{converted_parts[0]}]"
        return f'Union[{", ".join(converted_parts)}]'

    def _try_branded_scalar(self, ts_type: str) -> Optional[str]:
        if "&" in ts_type and "__brand" in ts_type:
            match = re.search(r"'__brand':\s*'([^']+)'", ts_type)
            if match:
                brand = match.group(1)
                return brand if brand.endswith("ID") else brand
        return None

    def _split_generic_args(self, inner: str) -> list[str]:
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
