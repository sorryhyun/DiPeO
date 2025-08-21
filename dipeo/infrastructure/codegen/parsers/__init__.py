"""Parser infrastructure for DiPeO.

This package contains the TypeScript parser for AST extraction.
"""

from .typescript.parser import TypeScriptParser

__all__ = [
    "TypeScriptParser",
]