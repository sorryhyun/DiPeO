"""Frontend-specific template filters for code generation.

This module provides filters specifically designed for generating frontend
TypeScript/JavaScript code, including UI field types, Zod schemas, and
TypeScript type declarations.
"""

from typing import Any


class FrontendFilters:
    """Collection of frontend-specific filters for code generation."""

    @classmethod
    def typescript_type(cls, field: dict[str, Any]) -> str:
        """Generate TypeScript type annotation for a field.

        Args:
            field: Field specification with type and properties

        Returns:
            TypeScript type string
        """
        field_name = field.get("name", "")
        ts_type = field.get("type", "any")
        is_required = field.get("required", False)
        is_array = field.get("isArray", False)

        # Handle array types
        if is_array:
            base_type = cls.typescript_type({**field, "isArray": False})
            ts_type = f"{base_type}[]"

        # Check for context-aware enum mappings first
        elif ts_type == "enum":
            # Map specific field names to their TypeScript enum types
            enum_mappings = {
                "method": "HttpMethod",
                "auth_type": "AuthType",
                "sub_type": "DBBlockSubType",
                "language": "SupportedLanguage",
                "code_type": "SupportedLanguage",
                "hook_type": "HookType",
                "trigger_mode": "HookTriggerMode",
                "service": "LLMService",
                "diagram_format": "DiagramFormat",
            }

            if field_name in enum_mappings:
                ts_type = enum_mappings[field_name]
            else:
                # Fall back to literal union type if enum values provided
                if field.get("enum"):
                    enum_values = field["enum"]
                    if isinstance(enum_values, list):
                        quoted = [f'"{v}"' if isinstance(v, str) else str(v) for v in enum_values]
                        ts_type = " | ".join(quoted)
                else:
                    ts_type = "string"  # Default to string for unknown enums

        # Handle special types
        else:
            type_map = {
                "string": "string",
                "number": "number",
                "boolean": "boolean",
                "object": "Record<string, any>",
                "dict": "Record<string, any>",
                "list": "any[]",
                "array": "any[]",
                "null": "null",
                "undefined": "undefined",
                "any": "any",
                "void": "void",
            }

            if ts_type in type_map:
                ts_type = type_map[ts_type]

        # Add optional modifier
        if not is_required:
            if not (ts_type.endswith(" | undefined") or "undefined" in ts_type.split("|")):
                ts_type = f"{ts_type} | undefined"

        return ts_type

    @classmethod
    def ui_field_type(cls, field: dict[str, Any]) -> str:
        """Determine UI field type for form generation.

        Maps field specifications to appropriate UI component types
        for React/frontend forms.

        Args:
            field: Field specification

        Returns:
            UI field type string
        """
        field_type = field.get("type", "text")
        field_name = field.get("name", "")
        ui_hint = field.get("uiType")

        if ui_hint:
            return ui_hint

        # Map based on field name patterns
        name_lower = field_name.lower()

        if any(x in name_lower for x in ["password", "secret", "token", "key"]):
            return "password"
        elif any(x in name_lower for x in ["email", "mail"]):
            return "text"  # Map email to text (no 'email' in FIELD_TYPES)
        elif any(x in name_lower for x in ["url", "link", "href"]):
            return "url"
        elif any(x in name_lower for x in ["phone", "tel", "mobile"]):
            return "text"  # Map tel to text (no 'tel' in FIELD_TYPES)
        elif any(x in name_lower for x in ["date", "birthday", "dob"]):
            return "text"  # Map date to text (no 'date' in FIELD_TYPES)
        elif any(x in name_lower for x in ["time", "hour", "minute"]):
            return "text"  # Map time to text (no 'time' in FIELD_TYPES)
        elif any(x in name_lower for x in ["color", "colour"]):
            return "text"  # Map color to text (no 'color' in FIELD_TYPES)
        elif any(x in name_lower for x in ["description", "content", "body", "message", "notes"]):
            return "textarea"
        elif field.get("enum"):
            return "select"
        elif field_type == "boolean":
            return "checkbox"
        elif field_type == "number" or field_type == "integer":
            return "number"
        elif field_type == "array" or field_type == "list":
            return "textarea"  # Map array to textarea (no 'array' in FIELD_TYPES)
        elif field_type == "object" or field_type == "dict":
            return "textarea"  # Map json/object to textarea (no 'json' in FIELD_TYPES)
        else:
            return "text"

    @classmethod
    def zod_schema(cls, field: dict[str, Any]) -> str:
        """Generate Zod validation schema for a field.

        Creates Zod schema definitions for runtime validation in TypeScript.

        Args:
            field: Field specification

        Returns:
            Zod schema string
        """
        # Ensure field is a dictionary
        if not isinstance(field, dict):
            return "z.any()"

        field_type = field.get("type", "string")
        is_required = field.get("required", False)
        is_array = field.get("isArray", False)
        validation = field.get("validation", {})

        # Ensure validation is a dictionary
        if not isinstance(validation, dict):
            validation = {}

        # Base type mapping
        type_map = {
            "string": "z.string()",
            "number": "z.number()",
            "boolean": "z.boolean()",
            "date": "z.date()",
            "object": "z.record(z.any())",
            "dict": "z.record(z.any())",
            "any": "z.any()",
            "null": "z.null()",
            "undefined": "z.undefined()",
        }

        schema = type_map.get(field_type, "z.any()")

        # Handle enums
        if field.get("enum"):
            enum_values = field["enum"]
            if isinstance(enum_values, list):
                quoted = [f'"{v}"' if isinstance(v, str) else str(v) for v in enum_values]
                schema = f"z.enum([{', '.join(quoted)}])"

        # Add validation constraints
        if field_type == "string":
            constraints = []
            if "minLength" in validation:
                constraints.append(f".min({validation['minLength']})")
            if "maxLength" in validation:
                constraints.append(f".max({validation['maxLength']})")
            if "pattern" in validation:
                # Escape forward slashes in the pattern for JavaScript regex literal
                pattern = validation["pattern"].replace("/", "\\/")
                constraints.append(f".regex(/{pattern}/)")
            if validation.get("email"):
                constraints.append(".email()")
            if validation.get("url"):
                constraints.append(".url()")

            if constraints:
                schema = f"z.string(){''.join(constraints)}"

        elif field_type == "number":
            constraints = []
            if "min" in validation:
                constraints.append(f".min({validation['min']})")
            if "max" in validation:
                constraints.append(f".max({validation['max']})")
            if validation.get("int") or validation.get("integer"):
                constraints.append(".int()")
            if validation.get("positive"):
                constraints.append(".positive()")
            if validation.get("negative"):
                constraints.append(".negative()")

            if constraints:
                schema = f"z.number(){''.join(constraints)}"

        # Handle arrays
        if is_array:
            schema = f"z.array({schema})"

        # Handle optional
        if not is_required:
            schema = f"{schema}.optional()"

        # Add description if present
        if field.get("description"):
            desc = field["description"].replace('"', '\\"')
            schema = f'{schema}.describe("{desc}")'

        return schema

    @classmethod
    def escape_js(cls, value: Any) -> str:
        """Escape a value for safe JavaScript string inclusion.

        Args:
            value: Value to escape

        Returns:
            Escaped string safe for JavaScript
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, int | float):
            return str(value)
        elif isinstance(value, str):
            # Escape special characters
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("'", "\\'")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
                .replace("\b", "\\b")
                .replace("\f", "\\f")
            )
            return f'"{escaped}"'
        elif isinstance(value, list | dict):
            import json

            return json.dumps(value)
        else:
            return str(value)

    @classmethod
    def get_enum_imports(cls, fields: list[dict[str, Any]]) -> list[str]:
        """Get list of enum types that need to be imported from @dipeo/models.

        Args:
            fields: List of field specifications

        Returns:
            List of unique enum type names to import
        """
        enum_mappings = {
            "method": "HttpMethod",
            "auth_type": "AuthType",
            "sub_type": "DBBlockSubType",
            "language": "SupportedLanguage",
            "code_type": "SupportedLanguage",
            "hook_type": "HookType",
            "trigger_mode": "HookTriggerMode",
            "service": "LLMService",
            "diagram_format": "DiagramFormat",
        }

        imports = set()
        for field in fields:
            if field.get("type") == "enum":
                field_name = field.get("name", "")
                if field_name in enum_mappings:
                    imports.add(enum_mappings[field_name])

        return sorted(list(imports))

    @classmethod
    def get_branded_type_imports(cls, fields: list[dict[str, Any]]) -> list[str]:
        """Get list of branded types that need to be imported from @dipeo/models.

        Branded types are nominal types like PersonID, NodeID, etc. that are defined
        in dipeo/models/src/core/diagram.ts.

        Args:
            fields: List of field specifications

        Returns:
            List of unique branded type names to import
        """
        branded_types = {
            "PersonID",
            "NodeID",
            "ArrowID",
            "HandleID",
            "ApiKeyID",
            "DiagramID",
            "HookID",
            "TaskID",
        }

        imports = set()
        for field in fields:
            field_type = field.get("type", "")
            if field_type in branded_types:
                imports.add(field_type)

        return sorted(list(imports))

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary.

        Only exports frontend-specific filters used in templates.
        """
        return {
            "typescript_type": cls.typescript_type,
            "ui_field_type": cls.ui_field_type,
            "zod_schema": cls.zod_schema,
            "escape_js": cls.escape_js,
            "get_enum_imports": cls.get_enum_imports,
            "get_branded_type_imports": cls.get_branded_type_imports,
        }
