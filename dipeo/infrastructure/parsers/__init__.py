"""Parser infrastructure for DiPeO.

This package contains parsers for various source code formats.
Each parser implements the ASTParserPort protocol.
"""

from .factory import ParserFactory
from .registry import ParserRegistry, parser_plugin
from .resource_locator import ParserResourceLocator

__all__ = [
    "ParserFactory",
    "ParserRegistry",
    "ParserResourceLocator",
    "parser_plugin",
]