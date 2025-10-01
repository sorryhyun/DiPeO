"""Shared type conversion utilities for the code generation pipeline.

NOTE: TypeConverter class has been removed. Use UnifiedTypeConverter from
dipeo.infrastructure.codegen.ir_builders.type_system_unified instead.

This module now only provides case conversion utilities.
"""

from __future__ import annotations

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