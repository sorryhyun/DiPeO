"""TypeScript to Python type conversion filters for code generation.

This module provides filters specifically designed for converting TypeScript
type annotations to Python type hints during code generation.
Uses infrastructure's type transformer for centralized type mappings.
"""

import os
import re
import sys
from typing import Any


def get_infrastructure_type_transformer():
    """Dynamically import type transformer from infrastructure."""
    try:
        # Ensure DIPEO_BASE_DIR is in path
        base_dir = os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO")
        if base_dir not in sys.path:
            sys.path.append(base_dir)

        from dipeo.infrastructure.parsers.typescript.type_transformer import map_ts_type_to_python

        return map_ts_type_to_python
    except ImportError:
        return None


class TypeScriptToPythonFilters:
    """Collection of filters for TypeScript to Python type conversion."""

    # Fallback type mapping (only used if infrastructure import fails)
    # This should eventually be removed once infrastructure is always available
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
        # Map deprecated execution status types to unified Status enum
        "ExecutionStatus": "Status",
        "NodeExecutionStatus": "Status",
    }

    # Fields that should be integers instead of floats
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

    # Branded ID types
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

    # Cache for converted types to improve performance
    _type_cache: dict[str, str] = {}

    @classmethod
    def ts_to_python_type(
        cls, ts_type: str, field_name: str = "", context: dict | None = None
    ) -> str:
        """Convert TypeScript type to Python type.

        Uses infrastructure's type transformer when available, falls back to legacy mapping.

        Args:
            ts_type: TypeScript type string
            field_name: Optional field name for context-specific conversions
            context: Optional context dict with additional info

        Returns:
            Python type string
        """
        if not ts_type:
            return "Any"

        # Check cache
        cache_key = f"{ts_type}:{field_name}"
        if cache_key in cls._type_cache:
            return cls._type_cache[cache_key]

        # Clean the type
        ts_type = cls.strip_inline_comments(ts_type).strip()

        # Handle boolean literals first (before infrastructure transformer)
        if ts_type == "true":
            result = "Literal[True]"
            cls._type_cache[cache_key] = result
            return result
        if ts_type == "false":
            result = "Literal[False]"
            cls._type_cache[cache_key] = result
            return result

        # Check for complex object types first (before infrastructure transformer)
        # These need special handling that infrastructure doesn't provide
        ts_type_stripped = ts_type.strip()
        if ts_type_stripped.startswith("{") and ts_type_stripped.endswith("}"):
            # Complex object literal - convert to Dict[str, Any]
            result = "Dict[str, Any]"
            cls._type_cache[cache_key] = result
            return result

        # Try to use infrastructure's type transformer for simple types
        infrastructure_transformer = get_infrastructure_type_transformer()
        if infrastructure_transformer:
            try:
                # Use infrastructure's centralized type mapping
                result = infrastructure_transformer(ts_type)

                # Apply field-specific overrides (e.g., integer fields)
                if result == "float" and field_name in cls.INTEGER_FIELDS:
                    result = "int"

                # Handle deprecated types that infrastructure might not know about
                if result in ["ExecutionStatus", "NodeExecutionStatus"]:
                    result = "Status"

                # Check if the result is still unconverted TypeScript
                # If it contains TypeScript syntax, it wasn't properly converted
                if result == ts_type:
                    # Infrastructure couldn't convert it, fall through to legacy handling
                    pass
                else:
                    # Successfully converted
                    cls._type_cache[cache_key] = result
                    return result
            except Exception:
                # Fall through to legacy implementation if infrastructure fails
                pass

        # Legacy implementation (fallback)
        # Handle complex object types with properties
        if ts_type.startswith("{") and ts_type.endswith("}"):
            result = "Dict[str, Any]"
            cls._type_cache[cache_key] = result
            return result

        # Handle optional types
        is_optional = False
        if ts_type.endswith(" | undefined") or ts_type.endswith(" | null"):
            base_type = ts_type.replace(" | undefined", "").replace(" | null", "").strip()
            is_optional = True
            result = cls.ts_to_python_type(base_type, field_name, context)
            if is_optional and not result.startswith("Optional["):
                result = f"Optional[{result}]"
            cls._type_cache[cache_key] = result
            return result

        # Handle arrays
        array_match = re.match(r"^(.+)\[\]$", ts_type)
        if array_match:
            inner_type = cls.ts_to_python_type(array_match.group(1), field_name, context)
            result = f"List[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        # Handle Array<T>
        generic_array_match = re.match(r"^Array<(.+)>$", ts_type, re.DOTALL)
        if generic_array_match:
            inner_type_str = generic_array_match.group(1).strip()

            # Special handling for inline object definitions with properties
            if inner_type_str.startswith("{") and inner_type_str.endswith("}"):
                # For complex inline objects, convert to Dict[str, Any]
                # This is a simplification since Python doesn't have inline type definitions
                result = "List[Dict[str, Any]]"
            else:
                inner_type = cls.ts_to_python_type(inner_type_str, field_name, context)
                result = f"List[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        # Handle Map/Record types
        map_match = re.match(r"^(Map|Record)<([^,]+),\s*(.+)>$", ts_type)
        if map_match:
            key_type = (
                "str"
                if map_match.group(2) in cls.BRANDED_IDS or map_match.group(2) == "string"
                else cls.ts_to_python_type(map_match.group(2))
            )
            value_type = cls.ts_to_python_type(map_match.group(3), field_name, context)
            result = f"Dict[{key_type}, {value_type}]"
            cls._type_cache[cache_key] = result
            return result

        # Handle literal types
        if re.match(r'^["\'\`].*["\'\`]$', ts_type) and "|" not in ts_type:
            literal_value = ts_type.strip("'\"`")
            result = f'Literal["{literal_value}"]'
            cls._type_cache[cache_key] = result
            return result

        # Handle union types
        if "|" in ts_type and not ts_type.startswith("("):
            parts = [cls.strip_inline_comments(p.strip()) for p in ts_type.split("|")]
            parts = [p for p in parts if p not in ["undefined", "null"]]

            if not parts:
                return "None"
            if len(parts) == 1:
                return cls.ts_to_python_type(parts[0], field_name, context)

            # Check if all parts are string literals
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
                    converted = cls.ts_to_python_type(part, field_name, context)
                    if converted not in converted_parts:
                        converted_parts.append(converted)
                result = f'Union[{", ".join(converted_parts)}]'

            cls._type_cache[cache_key] = result
            return result

        # Handle branded types
        if ts_type in cls.BRANDED_IDS:
            cls._type_cache[cache_key] = ts_type
            return ts_type

        # Handle basic types using fallback map
        if ts_type in cls.FALLBACK_TYPE_MAP:
            if ts_type == "number" and field_name in cls.INTEGER_FIELDS:
                result = "int"
            else:
                result = cls.FALLBACK_TYPE_MAP[ts_type]
            cls._type_cache[cache_key] = result
            return result

        # Handle empty object literal
        if ts_type == "{}":
            # Context-aware conversion for empty objects
            if field_name and context:
                result = cls.infer_empty_object_type(field_name, context)
            else:
                result = "Dict[str, Any]"
            cls._type_cache[cache_key] = result
            return result

        # Default to the type name (likely a custom type)
        cls._type_cache[cache_key] = ts_type
        return ts_type

    @staticmethod
    def strip_inline_comments(type_str: str) -> str:
        """Remove inline comments from TypeScript type strings."""
        if "//" in type_str:
            type_str = type_str.split("//")[0].strip()
        if "/*" in type_str and "*/" in type_str:
            type_str = re.sub(r"/\*.*?\*/", "", type_str).strip()
        return type_str

    @staticmethod
    def infer_empty_object_type(field_name: str, context: dict) -> str:
        """Infer the appropriate type for empty object based on field name."""
        field_lower = field_name.lower()

        # Check for list-like fields
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
        # Check for mapping fields
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

        # Handle complex types
        if py_type.startswith("List["):
            return "[]"
        elif py_type.startswith("Dict["):
            return "{}"
        elif py_type.startswith("Set["):
            return "set()"
        elif py_type.startswith("Tuple["):
            return "()"
        elif py_type in defaults:
            return defaults[py_type]
        else:
            return "None"

    @classmethod
    def clear_cache(cls):
        """Clear the type conversion cache."""
        cls._type_cache.clear()

    @classmethod
    def typescript_type(cls, field: dict[str, Any]) -> str:
        """Get TypeScript type from field definition."""
        field_type = field.get("type", "string")

        # Special handling for enum fields with values
        if field_type == "enum" and "values" in field:
            values = field.get("values", [])
            if values:
                # Generate union type from enum values
                return " | ".join(f"'{v}'" for v in values)
            else:
                return "string"  # Fallback if no values specified

        # Map to TypeScript type
        type_map = {
            "string": "string",
            "str": "string",
            "text": "string",
            "number": "number",
            "int": "number",
            "integer": "number",
            "float": "number",
            "bool": "boolean",
            "boolean": "boolean",
            "dict": "Record<string, any>",
            "object": "Record<string, any>",
            "list": "any[]",
            "array": "any[]",
            "any": "any",
            "null": "null",
            "undefined": "undefined",
            "void": "void",
        }

        # Handle array types
        if field_type.endswith("[]"):
            inner_type = field_type[:-2]
            return f"{cls.typescript_type({'type': inner_type})}[]"

        # Handle enum types without values
        if field_type.lower() == "enum":
            # Check if field has validation.allowedValues
            validation = field.get("validation", {})
            allowed_values = validation.get("allowedValues", [])

            # If allowedValues is a string (like "Object.values(MemoryProfile)"), try uiConfig.options
            if isinstance(allowed_values, str) and "uiConfig" in field:
                ui_config = field.get("uiConfig", {})
                options = ui_config.get("options", [])
                if options and isinstance(options, list):
                    # Extract values from options
                    values = [
                        opt.get("value")
                        for opt in options
                        if isinstance(opt, dict) and "value" in opt
                    ]
                    if values:
                        return " | ".join(f"'{v}'" for v in values)
            elif allowed_values and isinstance(allowed_values, list):
                # Generate union type from allowed values
                return " | ".join(f"'{v}'" for v in allowed_values)

            return "string"  # Fallback if no values specified

        return str(type_map.get(field_type.lower(), field_type))

    @classmethod
    def ui_field_type(cls, field: dict[str, Any]) -> str:
        """Get UI field type from field definition."""
        ui_config = field.get("uiConfig", {})
        if "inputType" in ui_config:
            return str(ui_config["inputType"])

        # Map field type to UI type
        field_type = field.get("type", "string")
        type_ui_map = {
            "string": "text",
            "str": "text",
            "text": "textarea",
            "number": "number",
            "int": "number",
            "integer": "number",
            "float": "number",
            "bool": "checkbox",
            "boolean": "checkbox",
            "array": "code",
            "list": "code",
            "object": "code",
            "dict": "code",
            "enum": "select",
            "select": "select",
            "date": "date",
            "datetime": "datetime",
            "time": "time",
            "file": "file",
            "password": "password",
            "email": "email",
            "url": "url",
            "color": "color",
        }

        return type_ui_map.get(field_type, "text")

    @classmethod
    def zod_schema(cls, field: dict[str, Any]) -> str:
        """Generate Zod schema for field validation."""
        field_type = field.get("type", "string")
        required = field.get("required", False)

        # Special handling for enum fields
        if field_type == "enum":
            # First check if field has direct values
            if "values" in field:
                values = field.get("values", [])
                if values:
                    # Generate z.enum() for enum fields
                    enum_values = ", ".join(f'"{v}"' for v in values)
                    base_schema = f"z.enum([{enum_values}])"
                else:
                    base_schema = "z.string()"
            else:
                # Check validation.allowedValues
                validation = field.get("validation", {})
                allowed_values = validation.get("allowedValues", [])

                # If allowedValues is a string (like "Object.values(MemoryProfile)"), try uiConfig.options
                if isinstance(allowed_values, str) and "uiConfig" in field:
                    ui_config = field.get("uiConfig", {})
                    options = ui_config.get("options", [])
                    if options and isinstance(options, list):
                        # Extract values from options
                        values = [
                            opt.get("value")
                            for opt in options
                            if isinstance(opt, dict) and "value" in opt
                        ]
                        if values:
                            enum_values = ", ".join(f'"{v}"' for v in values)
                            base_schema = f"z.enum([{enum_values}])"
                        else:
                            base_schema = "z.string()"
                    else:
                        base_schema = "z.string()"
                elif allowed_values and isinstance(allowed_values, list):
                    # Generate z.enum() from allowed values
                    enum_values = ", ".join(f'"{v}"' for v in allowed_values)
                    base_schema = f"z.enum([{enum_values}])"
                else:
                    base_schema = "z.string()"
        else:
            # Base schemas for other types
            schema_map = {
                "string": "z.string()",
                "str": "z.string()",
                "text": "z.string()",
                "number": "z.number()",
                "int": "z.number()",
                "integer": "z.number()",
                "float": "z.number()",
                "bool": "z.boolean()",
                "boolean": "z.boolean()",
                "array": "z.array(z.any())",
                "list": "z.array(z.any())",
                "object": "z.record(z.any())",
                "dict": "z.record(z.any())",
                "any": "z.any()",
                "null": "z.null()",
                "undefined": "z.undefined()",
            }

            base_schema = schema_map.get(field_type, "z.any()")

        # Add validation
        validations = []
        if field.get("validation"):
            val = field["validation"]
            if "min" in val:
                validations.append(f'.min({val["min"]})')
            if "max" in val:
                validations.append(f'.max({val["max"]})')
            if "pattern" in val:
                # Escape forward slashes in the pattern for JavaScript regex literal
                escaped_pattern = val["pattern"].replace("/", "\\/")
                validations.append(f".regex(/{escaped_pattern}/)")

        schema = base_schema + "".join(validations)

        # Handle optional
        if not required:
            schema += ".optional()"

        return schema

    @classmethod
    def escape_js(cls, value: Any) -> str:
        """Escape string for use in JavaScript."""
        if not isinstance(value, str):
            value = str(value)
        return (
            value.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary.

        Only exports filters actually used by codegen templates.
        Internal helper methods remain in the class but are not exported.
        """
        return {
            # Core conversion filters
            "ts_to_python": cls.ts_to_python_type,
            "to_py": cls.ts_to_python_type,  # Alias for backward compatibility
            "is_optional_ts": cls.is_optional_type,
            # Codegen-specific filters used in templates
            "typescript_type": cls.typescript_type,
            "ui_field_type": cls.ui_field_type,
            "zod_schema": cls.zod_schema,
            "escape_js": cls.escape_js,
        }
