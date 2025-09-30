"""Shared type system utilities for code generation components.

This module provides case conversion utilities for code generation.

NOTE: TypeConverter has been removed. Use UnifiedTypeConverter from
dipeo.infrastructure.codegen.ir_builders.type_system_unified instead.
"""

from .converter import (
    camel_case,
    camel_to_snake,
    kebab_case,
    pascal_case,
    pascal_to_camel,
    snake_case,
    snake_to_pascal,
)

__all__ = [
    "snake_case",
    "camel_case",
    "pascal_case",
    "kebab_case",
    "camel_to_snake",
    "snake_to_pascal",
    "pascal_to_camel",
]
