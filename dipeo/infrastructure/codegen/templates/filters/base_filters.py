"""Base template filters for general-purpose text transformations."""

import re

import inflection


class BaseFilters:
    @staticmethod
    def snake_case(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.underscore(str(text))

    @staticmethod
    def camel_case(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.camelize(str(text), uppercase_first_letter=False)

    @staticmethod
    def pascal_case(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.camelize(str(text))

    @staticmethod
    def kebab_case(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.dasherize(inflection.underscore(str(text)))

    @staticmethod
    def pluralize(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.pluralize(str(text))

    @staticmethod
    def singularize(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.singularize(str(text))

    @staticmethod
    def humanize(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.humanize(str(text))

    @staticmethod
    def titleize(text: str) -> str:
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.titleize(str(text))

    @staticmethod
    def ordinalize(number: int) -> str:
        return inflection.ordinalize(number)

    @staticmethod
    def indent_lines(text: str, spaces: int = 4) -> str:
        indent = " " * spaces
        return "\n".join(indent + line if line else line for line in text.splitlines())

    @staticmethod
    def quote_string(text: str, quote_char: str = '"') -> str:
        if quote_char == '"':
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif quote_char == "'":
            escaped = text.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        else:
            return text

    @staticmethod
    def join_lines(items: list[str], separator: str = "\n") -> str:
        return separator.join(items)

    @staticmethod
    def json_escape(text: str) -> str:
        import json

        return json.dumps(text)[1:-1]

    @staticmethod
    def regex_replace(text: str, pattern: str, replacement: str) -> str:
        return re.sub(pattern, replacement, text)

    @staticmethod
    def strip_prefix(text: str, prefix: str) -> str:
        return text[len(prefix) :] if text.startswith(prefix) else text

    @staticmethod
    def strip_suffix(text: str, suffix: str) -> str:
        return text[: -len(suffix)] if text.endswith(suffix) else text

    @staticmethod
    def wrap_lines(text: str, width: int = 80) -> str:
        import textwrap

        return textwrap.fill(text, width=width)

    @staticmethod
    def default_value(type_name: str, language: str = "python") -> str:
        defaults = {
            "python": {
                "str": '""',
                "int": "0",
                "float": "0.0",
                "bool": "False",
                "list": "[]",
                "dict": "{}",
                "set": "set()",
                "tuple": "()",
                "None": "None",
            },
            "typescript": {
                "string": '""',
                "number": "0",
                "boolean": "false",
                "array": "[]",
                "object": "{}",
                "null": "null",
                "undefined": "undefined",
            },
            "graphql": {
                "String": '""',
                "Int": "0",
                "Float": "0.0",
                "Boolean": "false",
                "ID": '""',
            },
        }

        lang_defaults = defaults.get(language, {})
        return lang_defaults.get(type_name, "null" if language == "typescript" else "None")

    @staticmethod
    def ensure_optional(type_str: str) -> str:
        """Ensure a type is properly wrapped with Optional, avoiding double wrapping."""
        if not type_str:
            return "Optional[Any]"

        # If already has Optional, return as-is
        if type_str.startswith("Optional["):
            return type_str

        # Otherwise, wrap with Optional
        return f"Optional[{type_str}]"

    @staticmethod
    def strip_optional(type_str: str) -> str:
        """Remove Optional wrapper from a type string."""
        if not type_str:
            return "Any"

        if type_str.startswith("Optional[") and type_str.endswith("]"):
            # Extract the inner type
            return type_str[9:-1]

        return type_str

    @classmethod
    def get_all_filters(cls) -> dict:
        filters = {}
        for name in dir(cls):
            if not name.startswith("_") and name != "get_all_filters":
                method = getattr(cls, name)
                if callable(method):
                    filters[name] = method
        return filters
