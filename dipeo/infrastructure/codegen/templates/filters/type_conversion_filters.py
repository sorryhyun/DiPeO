"""Type system conversion filters.

This module provides filters for type system conversions between TypeScript,
Python, and GraphQL during code generation.
"""

import re
from typing import Any

from dipeo.infrastructure.codegen.type_system import TypeConverter


class TypeConversionFilters:
    """Type system conversion filters."""

    FALLBACK_TYPE_MAP = {
        "string": "str",
        "number": "float",
        "boolean": "bool",
        "any": "Any",
        "unknown": "Any",
        "void": "None",
        "null": "None",
        "undefined": "None",
        "object": "Dict[str, Any]",
        "bigint": "int",
        "symbol": "str",
        "never": "Any",
        "ExecutionStatus": "Status",
        "NodeExecutionStatus": "Status",
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
    _converter = TypeConverter()

    @classmethod
    def ts_to_python(cls, ts_type: str, field_name: str = "") -> str:
        """Convert TypeScript type to Python type.

        Uses infrastructure's type transformer when available, falls back to legacy mapping.

        Args:
            ts_type: TypeScript type string
            field_name: Optional field name for context-specific conversions

        Returns:
            Python type string
        """
        if not ts_type:
            return "Any"

        cache_key = f"{ts_type}:{field_name}"
        if cache_key in cls._type_cache:
            return cls._type_cache[cache_key]

        ts_type = cls.strip_inline_comments(ts_type).strip()

        if ts_type == "true":
            result = "Literal[True]"
            cls._type_cache[cache_key] = result
            return result
        if ts_type == "false":
            result = "Literal[False]"
            cls._type_cache[cache_key] = result
            return result

        ts_type_stripped = ts_type.strip()
        if ts_type_stripped.startswith("{") and ts_type_stripped.endswith("}"):
            result = "Dict[str, Any]"
            cls._type_cache[cache_key] = result
            return result

        result = cls._converter.ts_to_python(ts_type)

        if result == "float" and field_name in cls.INTEGER_FIELDS:
            result = "int"

        if result in ["ExecutionStatus", "NodeExecutionStatus"]:
            result = "Status"

        if result != ts_type:
            cls._type_cache[cache_key] = result
            return result

        # Legacy implementation (fallback)
        if ts_type.startswith("{") and ts_type.endswith("}"):
            result = "Dict[str, Any]"
            cls._type_cache[cache_key] = result
            return result

        is_optional = False
        if ts_type.endswith(" | undefined") or ts_type.endswith(" | null"):
            base_type = ts_type.replace(" | undefined", "").replace(" | null", "").strip()
            is_optional = True
            result = cls.ts_to_python(base_type, field_name)
            if is_optional and not result.startswith("Optional["):
                result = f"Optional[{result}]"
            cls._type_cache[cache_key] = result
            return result

        array_match = re.match(r"^(.+)\[\]$", ts_type)
        if array_match:
            inner_type = cls.ts_to_python(array_match.group(1), field_name)
            result = f"List[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        generic_array_match = re.match(r"^Array<(.+)>$", ts_type, re.DOTALL)
        if generic_array_match:
            inner_type_str = generic_array_match.group(1).strip()

            if inner_type_str.startswith("{") and inner_type_str.endswith("}"):
                result = "List[Dict[str, Any]]"
            else:
                inner_type = cls.ts_to_python(inner_type_str, field_name)
                result = f"List[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        map_match = re.match(r"^(Map|Record)<([^,]+),\s*(.+)>$", ts_type)
        if map_match:
            key_type = (
                "str"
                if map_match.group(2) in cls.BRANDED_IDS or map_match.group(2) == "string"
                else cls.ts_to_python(map_match.group(2))
            )
            value_type = cls.ts_to_python(map_match.group(3), field_name)
            result = f"Dict[{key_type}, {value_type}]"
            cls._type_cache[cache_key] = result
            return result

        if re.match(r'^["\'\`].*["\'\`]$', ts_type) and "|" not in ts_type:
            literal_value = ts_type.strip("'\"`")
            result = f'Literal["{literal_value}"]'
            cls._type_cache[cache_key] = result
            return result

        if "|" in ts_type and not ts_type.startswith("("):
            parts = [cls.strip_inline_comments(p.strip()) for p in ts_type.split("|")]
            parts = [p for p in parts if p not in ["undefined", "null"]]

            if not parts:
                return "None"
            if len(parts) == 1:
                return cls.ts_to_python(parts[0], field_name)

            all_literals = all(re.match(r'^["\'\`].*["\'\`]$', p.strip()) for p in parts)
            all_numeric = all(p.strip().replace("-", "").replace(".", "").isdigit() for p in parts)

            if all_literals:
                literal_values = [p.strip().strip("'\"`") for p in parts]
                quoted_values = ", ".join(f'"{v}"' for v in literal_values)
                result = f"Literal[{quoted_values}]"
            elif all_numeric:
                numeric_values = ", ".join(p.strip() for p in parts)
                result = f"Literal[{numeric_values}]"
            else:
                converted_parts = []
                for part in parts:
                    converted = cls.ts_to_python(part, field_name)
                    if converted not in converted_parts:
                        converted_parts.append(converted)
                result = f'Union[{", ".join(converted_parts)}]'

            cls._type_cache[cache_key] = result
            return result

        if ts_type in cls.BRANDED_IDS:
            cls._type_cache[cache_key] = ts_type
            return ts_type

        if ts_type in cls.FALLBACK_TYPE_MAP:
            if ts_type == "number" and field_name in cls.INTEGER_FIELDS:
                result = "int"
            else:
                result = cls.FALLBACK_TYPE_MAP[ts_type]
            cls._type_cache[cache_key] = result
            return result

        cls._type_cache[cache_key] = ts_type
        return ts_type

    @classmethod
    def graphql_to_python(cls, graphql_type: str, required: bool = True) -> str:
        """Convert GraphQL type to Python type.

        Args:
            graphql_type: GraphQL type string (e.g., 'ID', 'String', 'Int')
            required: Whether the field is required

        Returns:
            Python type string
        """
        python_type = cls._converter.graphql_to_python(graphql_type)

        # Maintain legacy lowercase list typing for backwards compatibility
        if python_type.startswith("List["):
            python_type = "list" + python_type[4:]

        if not required and not graphql_type.endswith("!"):
            if not python_type.startswith("Optional["):
                python_type = f"Optional[{python_type}]"

        return python_type

    @classmethod
    def python_type_with_context(
        cls, field: dict[str, Any], node_type: str, mappings: dict[str, Any] | None = None
    ) -> str:
        """Convert field type to Python type with context awareness."""
        field_name = field.get("name", "")
        field_type = field.get("type", "string")
        is_required = field.get("required", False)

        base_type = None

        context_mappings = {
            "method": "HttpMethod",
            "sub_type": "DBBlockSubType",
            "language": "SupportedLanguage",
            "code_type": "SupportedLanguage",
            "hook_type": "HookType",
            "trigger_mode": "HookTriggerMode",
            "service": "LLMService",
            "diagram_format": "DiagramFormat",
        }

        if field_name in context_mappings:
            base_type = context_mappings[field_name]
        elif mappings and "ts_to_py_type" in mappings and field_type in mappings["ts_to_py_type"]:
            base_type = str(mappings["ts_to_py_type"][field_type])
        elif node_type == "person_job":
            if field_name == "person_id":
                base_type = "PersonID"
            elif field_name == "llm_config":
                base_type = "PersonLLMConfig"
            elif field_name == "memory_settings":
                base_type = "MemorySettings"
            elif field_name == "memory_profile":
                base_type = "str"
            elif field_name == "tools":
                base_type = "List[ToolConfig]"

        if base_type is None:
            if field_name == "maxIteration" or field_name == "max_iteration":
                base_type = "int"
            elif field_type == "object" or field_type == "dict":
                base_type = "Dict[str, Any]"
            elif field_type == "array" or field_type == "list":
                base_type = "List[Any]"
            elif field_type == "string":
                base_type = "str"
            elif field_type == "number":
                if field_name in cls.INTEGER_FIELDS:
                    base_type = "int"
                else:
                    base_type = "float"
            elif field_type == "boolean":
                base_type = "bool"
            elif field_type == "enum":
                values = field.get("values", [])
                if not values and field.get("validation"):
                    values = field.get("validation", {}).get("allowedValues", [])

                if values:
                    quoted_values = ", ".join(f'"{v}"' for v in values)
                    base_type = f"Literal[{quoted_values}]"
                else:
                    base_type = "str"
            elif field_type == "any":
                base_type = "Any"
            else:
                base_type = field_type

        if not is_required:
            if field_type in ["object", "dict", "array", "list"]:
                return f"Optional[{base_type}]"
            if "default" in field and field["default"] is not None:
                return base_type
            return f"Optional[{base_type}]"

        return base_type

    @classmethod
    def ts_graphql_input_to_python(cls, ts_type: str, field_name: str = "") -> str:
        """Convert TypeScript GraphQL input syntax to Python type.

        Handles special GraphQL input patterns:
        - Scalars['Type']['input'] → Python type
        - InputMaybe<T> → Optional[T]
        - Array<T> → List[T]
        - References to other input types

        Args:
            ts_type: TypeScript GraphQL input type string
            field_name: Optional field name for context

        Returns:
            Python type string
        """
        if not ts_type:
            return "JSON"  # Default to JSON instead of Any for GraphQL

        ts_type = ts_type.strip()

        # Handle Scalars['Type']['input'] pattern
        scalars_match = re.match(r"Scalars\['(\w+)'\]\['input'\]", ts_type)
        if scalars_match:
            scalar_type = scalars_match.group(1)
            # Map GraphQL scalar types to Python
            scalar_map = {
                "ID": "str",  # GraphQL ID is a string in Python
                "String": "str",
                "Int": "int",
                "Float": "float",
                "Boolean": "bool",
                "DateTime": "datetime",
                "Date": "datetime",
                "Time": "str",
                "JSON": "JSON",  # Map to strawberry.scalars.JSON
                "BigInt": "int",
            }
            return scalar_map.get(scalar_type, scalar_type)

        # Handle InputMaybe<T> pattern
        input_maybe_match = re.match(r"InputMaybe<(.+)>", ts_type, re.DOTALL)
        if input_maybe_match:
            inner_type = input_maybe_match.group(1).strip()
            # Recursively convert the inner type
            python_type = cls.ts_graphql_input_to_python(inner_type, field_name)
            # InputMaybe means Optional in Python
            if not python_type.startswith("Optional["):
                return f"Optional[{python_type}]"
            return python_type

        # Handle Array<T> pattern
        array_match = re.match(r"Array<(.+)>", ts_type, re.DOTALL)
        if array_match:
            inner_type = array_match.group(1).strip()
            # Recursively convert the inner type
            python_type = cls.ts_graphql_input_to_python(inner_type, field_name)
            return f"List[{python_type}]"

        # Handle Maybe<T> pattern (similar to InputMaybe)
        maybe_match = re.match(r"Maybe<(.+)>", ts_type, re.DOTALL)
        if maybe_match:
            inner_type = maybe_match.group(1).strip()
            python_type = cls.ts_graphql_input_to_python(inner_type, field_name)
            if not python_type.startswith("Optional["):
                return f"Optional[{python_type}]"
            return python_type

        # Handle input type references (e.g., Vec2Input, PersonLLMConfigInput)
        if ts_type.endswith("Input"):
            # These are references to other input types, keep as-is
            return ts_type

        # Handle branded ID types
        if ts_type in cls.BRANDED_IDS:
            return "str"  # All branded IDs are strings in Python

        # Handle special field names that should be JSON
        json_field_names = {
            "data",
            "variables",
            "metadata",
            "output",
            "input",
            "diagram_data",
            "node_data",
            "body",
            "headers",
            "params",
            "config",
            "options",
            "settings",
            "props",
            "properties",
        }

        # If field name suggests JSON data, use JSON type
        if field_name in json_field_names or field_name.endswith("_data"):
            if ts_type in ["any", "Any", "unknown", "object", "{}", "Record<string, any>"]:
                return "JSON"

        # Handle primitive types
        primitive_map = {
            "string": "str",
            "number": "float",
            "boolean": "bool",
            "any": "JSON",  # Map 'any' to JSON for GraphQL compatibility
            "unknown": "JSON",  # Map 'unknown' to JSON
            "object": "JSON",  # Map 'object' to JSON
            "void": "None",
            "null": "None",
            "undefined": "None",
        }

        if ts_type in primitive_map:
            mapped = primitive_map[ts_type]
            # Check for integer fields
            if mapped == "float" and field_name in cls.INTEGER_FIELDS:
                return "int"
            return mapped

        # Handle T[] array syntax
        array_suffix_match = re.match(r"^(.+)\[\]$", ts_type)
        if array_suffix_match:
            inner_type = array_suffix_match.group(1)
            python_type = cls.ts_graphql_input_to_python(inner_type, field_name)
            return f"List[{python_type}]"

        # Handle Record<K, V> pattern - should map to JSON
        record_match = re.match(r"Record<(.+),\s*(.+)>", ts_type)
        if record_match:
            return "JSON"

        # Handle Dict pattern - should map to JSON
        if ts_type.startswith("Dict") or ts_type.startswith("dict"):
            return "JSON"

        # Default: return as-is (likely a type reference)
        return ts_type

    @classmethod
    def ensure_optional(cls, type_str: str) -> str:
        """Ensure a type is wrapped in Optional if not already."""
        if not type_str or type_str.startswith("Optional["):
            return type_str
        return f"Optional[{type_str}]"

    @staticmethod
    def strip_inline_comments(type_str: str) -> str:
        """Strip inline comments from type strings."""
        if "//" in type_str:
            type_str = type_str.split("//")[0].strip()
        if "/*" in type_str and "*/" in type_str:
            type_str = re.sub(r"/\*.*?\*/", "", type_str).strip()
        return type_str

    @staticmethod
    def infer_empty_object_type(field_name: str, context: dict | None = None) -> str:
        """Infer the appropriate type for empty object based on field name."""
        field_lower = field_name.lower()

        if "indices" in field_lower and "node" in field_lower:
            return "List[int]"
        elif any(x in field_lower for x in ["tools", "tags", "args", "env", "params", "headers"]):
            return "List[str]"
        elif field_lower in [
            "messages",
            "nodes",
            "handles",
            "arrows",
            "persons",
            "fields",
            "inputs",
            "outputs",
            "examples",
            "items",
            "elements",
        ]:
            return "List[Any]"
        elif any(
            x in field_lower
            for x in [
                "config",
                "options",
                "settings",
                "metadata",
                "props",
                "properties",
                "attributes",
            ]
        ):
            return "Dict[str, Any]"
        else:
            return "Dict[str, Any]"

    @classmethod
    def get_python_imports(cls, types_used: list[str]) -> list[str]:
        """Generate Python import statements based on types used."""
        imports = set()

        for type_str in types_used:
            if "List[" in type_str:
                imports.add("from typing import List")
            if "Dict[" in type_str:
                imports.add("from typing import Dict")
            if "Optional[" in type_str:
                imports.add("from typing import Optional")
            if "Union[" in type_str:
                imports.add("from typing import Union")
            if "Literal[" in type_str:
                imports.add("from typing import Literal")
            if "Any" in type_str:
                imports.add("from typing import Any")
            if "Tuple[" in type_str:
                imports.add("from typing import Tuple")
            if "Set[" in type_str:
                imports.add("from typing import Set")

        return sorted(list(imports))

    @classmethod
    def is_optional_type(cls, ts_type: str) -> bool:
        """Check if a TypeScript type is optional."""
        ts_type = ts_type.strip()
        return (
            ts_type.endswith(" | undefined")
            or ts_type.endswith(" | null")
            or "undefined" in ts_type.split("|")
            or "null" in ts_type.split("|")
        )

    @classmethod
    def is_branded_type(cls, type_name: str) -> bool:
        """Check if a type is a branded ID type."""
        return type_name in cls.BRANDED_IDS

    @classmethod
    def get_default_value(cls, py_type: str, is_optional: bool = False) -> str:
        """Get appropriate default value for a Python type."""
        if is_optional:
            return "None"

        defaults = {
            "str": '""',
            "int": "0",
            "float": "0.0",
            "bool": "False",
            "None": "None",
        }

        if py_type.startswith("List["):
            return "[]"
        elif py_type.startswith("Dict["):
            return "{}"
        elif py_type.startswith("Set["):
            return "set()"
        elif py_type.startswith("Tuple["):
            return "()"
        elif py_type.startswith("Optional["):
            return "None"

        return defaults.get(py_type, "None")

    @classmethod
    def clear_cache(cls):
        """Clear the type conversion cache."""
        cls._type_cache.clear()

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary."""
        return {
            "ts_to_python": cls.ts_to_python,
            "graphql_to_python": cls.graphql_to_python,
            "python_type_with_context": cls.python_type_with_context,
            "ts_graphql_input_to_python": cls.ts_graphql_input_to_python,
            "ensure_optional": cls.ensure_optional,
            "strip_inline_comments": cls.strip_inline_comments,
            "infer_empty_object_type": cls.infer_empty_object_type,
            "get_python_imports": cls.get_python_imports,
            "is_optional_type": cls.is_optional_type,
            "is_branded_type": cls.is_branded_type,
            "get_default_value": cls.get_default_value,
            "clear_cache": cls.clear_cache,
        }
