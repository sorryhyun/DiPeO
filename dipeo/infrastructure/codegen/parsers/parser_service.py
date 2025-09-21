"""TypeScript-only parser service."""

import logging
from pathlib import Path
from typing import Any

from dipeo.domain.base.mixins import (
    CachingMixin,
    ConfigurationMixin,
    InitializationMixin,
    LoggingMixin,
)
from dipeo.domain.integrations.ports import ASTParserPort
from dipeo.infrastructure.codegen.parsers.typescript.parser import TypeScriptParser

logger = logging.getLogger(__name__)


class ParserService(
    LoggingMixin, InitializationMixin, ConfigurationMixin, CachingMixin, ASTParserPort
):
    """TypeScript-only parser service.

    This service provides AST parsing specifically for TypeScript/JavaScript
    code, supporting both single file and batch operations.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the parser service.

        Args:
            config: Optional configuration dict. Can contain:
                - project_root: Project root directory path
                - cache_enabled: Whether to enable AST caching (default: True)
        """
        InitializationMixin.__init__(self)
        ConfigurationMixin.__init__(self, config)
        CachingMixin.__init__(self)
        self._project_root = self.get_config_value("project_root")
        self._cache_enabled = self.get_config_value("cache_enabled", True)
        self._ts_parser: TypeScriptParser | None = None

    async def initialize(self) -> None:
        """Initialize the service and create TypeScript parser.

        This method is called during service startup and ensures
        the TypeScript parser is ready for immediate use.
        """
        self._ts_parser = TypeScriptParser(
            project_root=self._project_root, cache_enabled=self._cache_enabled
        )

    async def parse(
        self, source: str, extract_patterns: list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse TypeScript source code and extract AST information.

        Args:
            source: The source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options. Can include:
                - includeJSDoc: Whether to include JSDoc comments
                - parseMode: 'module' or 'script'

        Returns:
            Dictionary containing AST data and metadata
        """
        if not self._ts_parser:
            await self.initialize()

        try:
            result = await self._ts_parser.parse(source, extract_patterns, options or {})
            return result
        except Exception as e:
            logger.error(f"[ParserService] Parse failed: {e!s}")
            raise

    async def parse_file(
        self, file_path: str, extract_patterns: list[str], options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse a TypeScript source file.

        Args:
            file_path: Path to the source file (relative to project root)
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options

        Returns:
            Same as parse() method
        """
        if not self._ts_parser:
            await self.initialize()

        if hasattr(self._ts_parser, "parse_file"):
            return await self._ts_parser.parse_file(file_path, extract_patterns, options or {})
        else:
            file_full_path = Path(self._project_root or ".") / file_path
            with open(file_full_path) as f:
                source = f.read()
            return await self._ts_parser.parse(source, extract_patterns, options or {})

    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript sources in a single operation.

        Args:
            sources: Dictionary mapping keys to source code
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options

        Returns:
            Dictionary mapping each key to its parse result
        """
        if not self._ts_parser:
            await self.initialize()

        return await self._ts_parser.parse_batch(sources, extract_patterns, options or {})

    async def parse_files_batch(
        self,
        file_paths: list[str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript files in a single operation.

        Args:
            file_paths: List of file paths relative to project root
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options

        Returns:
            Dictionary mapping file paths to parse results
        """
        if not self._ts_parser:
            await self.initialize()

        if hasattr(self._ts_parser, "parse_files_batch"):
            return await self._ts_parser.parse_files_batch(
                file_paths, extract_patterns, options or {}
            )
        else:
            results = {}
            for path in file_paths:
                results[path] = await self.parse_file(path, extract_patterns, options)
            return results

    def clear_cache(self, language: str | None = None):
        """Clear TypeScript parser cache.

        Args:
            language: Ignored - this service is TypeScript-only
        """
        if self._ts_parser and hasattr(self._ts_parser, "clear_cache"):
            self._ts_parser.clear_cache()


def get_parser_service(
    project_root: Path | None = None, cache_enabled: bool = True
) -> ParserService:
    """Factory function to create TypeScript parser service.

    Args:
        project_root: Optional project root directory
        cache_enabled: Whether to enable caching

    Returns:
        A configured parser service instance
    """
    config = {"cache_enabled": cache_enabled}
    if project_root:
        config["project_root"] = project_root

    return ParserService(config=config)
