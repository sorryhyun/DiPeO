"""TypeScript to GraphQL type conversion filters for code generation.

This module provides filters specifically designed for converting TypeScript
type annotations to GraphQL type definitions during schema generation.
"""

import re
from typing import Any


class TypeScriptToGraphQLFilters:
    """Collection of filters for TypeScript to GraphQL type conversion."""

    TYPE_MAP = {
        "string": "String",
        "number": "Float",
        "boolean": "Boolean",
        "any": "JSON",
        "unknown": "JSON",
        "void": "JSON",
        "null": "JSON",
        "undefined": "JSON",
        "object": "JSON",
        "bigint": "BigInt",
        "symbol": "String",
        "never": "JSON",
        "Date": "DateTime",
    }

    INTEGER_FIELDS = {
        "maxIteration",
        "sequence",
        "messageCount",
        "timeout",
        "timeoutSeconds",
        "durationSeconds",
        "maxTokens",
        "statusCode",
        "totalTokens",
        "promptTokens",
        "completionTokens",
        "input",
        "output",
        "cached",
        "total",
        "retries",
        "maxRetries",
        "port",
        "x",
        "y",
        "width",
        "height",
        "count",
        "index",
        "limit",
        "offset",
        "page",
        "pageSize",
        "size",
        "length",
        "version",
    }

    BRANDED_IDS = {
        "NodeID",
        "ArrowID",
        "HandleID",
        "PersonID",
        "ApiKeyID",
        "DiagramID",
        "ExecutionID",
        "HookID",
        "TaskID",
        "MessageID",
        "ConversationID",
        "AgentID",
        "ToolID",
        "FileID",
    }

    _type_cache: dict[str, str] = {}

    @classmethod
    def ts_to_graphql_type(
        cls, ts_type: str, field_name: str = "", context: dict | None = None
    ) -> str:
        """Convert TypeScript type to GraphQL type.

        Args:
            ts_type: TypeScript type string
            field_name: Optional field name for context-specific conversions
            context: Optional context dict with additional info

        Returns:
            GraphQL type string
        """
        if not ts_type:
            return "JSON"

        cache_key = f"{ts_type}:{field_name}"
        if cache_key in cls._type_cache:
            return cls._type_cache[cache_key]

        ts_type = cls.strip_inline_comments(ts_type).strip()

        if ts_type in cls.BRANDED_IDS:
            cls._type_cache[cache_key] = "ID"
            return "ID"

        if ts_type.startswith("{") and ts_type.endswith("}"):
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        if " | " in ts_type:
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        array_match = re.match(r"^(.+)\[\]$", ts_type)
        if array_match:
            inner_type = cls.ts_to_graphql_type(array_match.group(1), field_name, context)
            result = f"[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        generic_array_match = re.match(r"^Array<(.+)>$", ts_type)
        if generic_array_match:
            inner_type = cls.ts_to_graphql_type(generic_array_match.group(1), field_name, context)
            result = f"[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        record_match = re.match(r"^Record<(.+),\s*(.+)>$", ts_type)
        if record_match:
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        base_type = cls.TYPE_MAP.get(ts_type, ts_type)

        if base_type == "Float" and field_name in cls.INTEGER_FIELDS:
            base_type = "Int"

        cls._type_cache[cache_key] = base_type
        return base_type

    @classmethod
    def strip_inline_comments(cls, text: str) -> str:
        return re.sub(r"//.*$", "", text, flags=re.MULTILINE).strip()

    @classmethod
    def graphql_field_type(cls, field: dict[str, Any]) -> str:
        """Generate GraphQL field type from TypeScript field definition.

        Args:
            field: Field definition dict with 'type' and optionally 'required'

        Returns:
            GraphQL field type string with nullability
        """
        ts_type = field.get("type", "JSON")
        field_name = field.get("name", "")
        required = field.get("required", False)

        graphql_type = cls.ts_to_graphql_type(ts_type, field_name)

        if (required and not graphql_type.startswith("[")) or (
            required and graphql_type.startswith("[")
        ):
            graphql_type = f"{graphql_type}!"

        return graphql_type

    @classmethod
    def graphql_input_type_name(cls, type_name: str) -> str:
        if type_name.endswith("Type"):
            return type_name.replace("Type", "Input")
        return f"{type_name}Input"

    @classmethod
    def graphql_enum_value(cls, value: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", value.upper())

    @classmethod
    def get_all_filters(cls) -> dict[str, Any]:
        """Get all filters provided by this class."""
        return {
            "ts_to_graphql_type": cls.ts_to_graphql_type,
            "graphql_field_type": cls.graphql_field_type,
            "graphql_input_type_name": cls.graphql_input_type_name,
            "graphql_enum_value": cls.graphql_enum_value,
            "strip_inline_comments": cls.strip_inline_comments,
        }
