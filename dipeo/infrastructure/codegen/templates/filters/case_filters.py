"""Text case transformation filters."""

import inflection


class CaseFilters:
    """Text case transformation filters."""

    @staticmethod
    def snake_case(text: str) -> str:
        """Convert text to snake_case format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.underscore(str(text))

    @staticmethod
    def pascal_case(text: str) -> str:
        """Convert text to PascalCase format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.camelize(str(text))

    @staticmethod
    def camel_case(text: str) -> str:
        """Convert text to camelCase format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.camelize(str(text), uppercase_first_letter=False)

    @staticmethod
    def kebab_case(text: str) -> str:
        """Convert text to kebab-case format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return inflection.dasherize(inflection.underscore(str(text)))

    @staticmethod
    def upper(text: str) -> str:
        """Convert text to UPPERCASE format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return str(text).upper()

    @staticmethod
    def lower(text: str) -> str:
        """Convert text to lowercase format."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return str(text).lower()

    @staticmethod
    def capitalize(text: str) -> str:
        """Convert text to Capitalized format (first letter uppercase)."""
        if text is None or text == "" or str(text) == "Undefined":
            return ""
        return str(text).capitalize()

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary."""
        return {
            "snake_case": cls.snake_case,
            "pascal_case": cls.pascal_case,
            "camel_case": cls.camel_case,
            "kebab_case": cls.kebab_case,
            "upper": cls.upper,
            "lower": cls.lower,
            "capitalize": cls.capitalize,
        }
