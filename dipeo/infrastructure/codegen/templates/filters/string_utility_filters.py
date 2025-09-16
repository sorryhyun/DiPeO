"""General string manipulation filters."""

import re

import inflection


class StringUtilityFilters:
    """General string manipulation filters."""

    @staticmethod
    def pluralize(text: str) -> str:
        """Convert text to plural form."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.pluralize(str(text))

    @staticmethod
    def singularize(text: str) -> str:
        """Convert text to singular form."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.singularize(str(text))

    @staticmethod
    def humanize(text: str) -> str:
        """Convert text to human-readable form."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.humanize(str(text))

    @staticmethod
    def escape_js(text: str) -> str:
        """Escape string for use in JavaScript."""
        if not isinstance(text, str):
            text = str(text)
        return (
            text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

    @staticmethod
    def strip_inline_comments(text: str) -> str:
        """Strip inline comments from text."""
        if "//" in text:
            text = text.split("//")[0].strip()
        if "/*" in text and "*/" in text:
            text = re.sub(r"/\*.*?\*/", "", text).strip()
        return text

    @staticmethod
    def join(items: list, separator: str = "") -> str:
        """Join a list of items with a separator."""
        if not isinstance(items, list):
            return str(items)
        return separator.join(str(item) for item in items)

    @staticmethod
    def replace(text: str, old: str, new: str) -> str:
        """Replace all occurrences of old with new in text."""
        if not isinstance(text, str):
            text = str(text)
        return text.replace(old, new)

    @staticmethod
    def default(value, default_value=""):
        """Return default value if value is None, empty, or falsy."""
        if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
            return default_value
        return value

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary."""
        return {
            "pluralize": cls.pluralize,
            "singularize": cls.singularize,
            "humanize": cls.humanize,
            "escape_js": cls.escape_js,
            "strip_inline_comments": cls.strip_inline_comments,
            "join": cls.join,
            "replace": cls.replace,
            "default": cls.default,
        }
