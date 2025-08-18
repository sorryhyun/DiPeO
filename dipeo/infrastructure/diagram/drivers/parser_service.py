"""Generic parser service supporting multiple programming languages."""

import logging
from pathlib import Path
from typing import Any

from dipeo.domain.base import BaseService
from dipeo.domain.parsers.ports import ASTParserPort
from dipeo.infrastructure.parsers.factory import ParserFactory
from dipeo.infrastructure.config.parser_config import ParserConfig

logger = logging.getLogger(__name__)


class ParserService(BaseService, ASTParserPort):
    """Generic parser service supporting multiple programming languages.
    
    This service provides a unified interface for parsing different programming
    languages, delegating to appropriate language-specific parsers via the factory.
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the parser service.
        
        Args:
            config: Optional configuration dict. Can contain:
                - default_language: Default programming language (default: typescript)
                - project_root: Project root directory path
                - cache_enabled: Whether to enable AST caching (default: True)
                - log_level: Logging level for parser operations
        """
        super().__init__(config)
        self._parsers: dict[str, ASTParserPort] = {}
        self._factory = ParserFactory()
        self._default_language = self.get_config_value("default_language", "typescript")
        self._project_root = self.get_config_value("project_root")
        self._cache_enabled = self.get_config_value("cache_enabled", True)
    
    async def initialize(self) -> None:
        """Initialize the service and pre-load default parser.
        
        This method is called during service startup and ensures
        the default parser is ready for immediate use.
        """
        if self._default_language:
            logger.debug(f"Pre-initializing default parser: {self._default_language}")
            await self._get_or_create_parser(self._default_language)
    
    async def parse(
        self,
        source: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse source code and extract AST information.
        
        Args:
            source: The source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options. Can include:
                - language: Programming language (defaults to service's default_language)
                - includeJSDoc: Whether to include JSDoc comments (TypeScript)
                - parseMode: 'module' or 'script' (TypeScript)
                
        Returns:
            Dictionary containing AST data and metadata
        """
        options = options or {}
        language = options.get("language", self._default_language)

        try:
            parser = await self._get_or_create_parser(language)
            result = await parser.parse(source, extract_patterns, options)
            return result
        except Exception as e:
            logger.error(f"[ParserService] Parse failed: {str(e)}")
            raise
    
    async def parse_file(
        self,
        file_path: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse a source file.
        
        Args:
            file_path: Path to the source file (relative to project root)
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options, including 'language'
            
        Returns:
            Same as parse() method
        """
        options = options or {}
        language = options.get("language", self._default_language)
        
        # Auto-detect language from file extension if not specified
        if not language and '.' in file_path:
            language = self._detect_language_from_extension(file_path)
            options["language"] = language
        
        parser = await self._get_or_create_parser(language)
        
        # Check if parser has a parse_file method
        if hasattr(parser, 'parse_file'):
            return await parser.parse_file(file_path, extract_patterns, options)
        else:
            # Fallback: read file and use parse method
            from pathlib import Path
            file_full_path = Path(self._project_root or '.') / file_path
            with open(file_full_path, 'r') as f:
                source = f.read()
            return await parser.parse(source, extract_patterns, options)
    
    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple sources in a single operation.
        
        Args:
            sources: Dictionary mapping keys to source code
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping each key to its parse result
        """
        options = options or {}
        language = options.get("language", self._default_language)
        
        parser = await self._get_or_create_parser(language)
        
        # Check if parser has a parse_batch method
        if hasattr(parser, 'parse_batch'):
            return await parser.parse_batch(sources, extract_patterns, options)
        else:
            # Fallback: parse individually
            results = {}
            for key, source in sources.items():
                results[key] = await parser.parse(source, extract_patterns, options)
            return results
    
    async def parse_files_batch(
        self,
        file_paths: list[str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple files in a single operation.
        
        Args:
            file_paths: List of file paths relative to project root
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping file paths to parse results
        """
        options = options or {}
        
        # Group files by detected language
        files_by_language: dict[str, list[str]] = {}
        for file_path in file_paths:
            language = options.get("language") or self._detect_language_from_extension(file_path)
            if language not in files_by_language:
                files_by_language[language] = []
            files_by_language[language].append(file_path)
        
        # Parse each language group
        all_results = {}
        for language, paths in files_by_language.items():
            parser = await self._get_or_create_parser(language)
            
            if hasattr(parser, 'parse_files_batch'):
                results = await parser.parse_files_batch(paths, extract_patterns, options)
                all_results.update(results)
            else:
                # Fallback: parse individually
                for path in paths:
                    all_results[path] = await self.parse_file(path, extract_patterns, options)
        
        return all_results
    
    def clear_cache(self, language: str | None = None):
        """Clear parser cache.
        
        Args:
            language: Clear cache for specific language, or all if None
        """
        if language:
            if language in self._parsers:
                parser = self._parsers[language]
                if hasattr(parser, 'clear_cache'):
                    parser.clear_cache()
        else:
            # Clear all parser caches
            for lang, parser in self._parsers.items():
                if hasattr(parser, 'clear_cache'):
                    parser.clear_cache()

    async def _get_or_create_parser(self, language: str) -> ASTParserPort:
        """Get existing parser or create new one for language.
        
        Args:
            language: Programming language name
            
        Returns:
            Parser instance for the language
        """
        if language not in self._parsers:

            if self._project_root:
                config = ParserConfig.from_dict(
                    {"project_root": self._project_root, "cache_enabled": self._cache_enabled},
                    language
                )
            else:
                config = ParserConfig.from_env(language)
                config.cache_enabled = self._cache_enabled
            
            self._parsers[language] = self._factory.create_parser(config)
            
            # Initialize if it has an initialize method
            parser = self._parsers[language]
            if hasattr(parser, 'initialize'):
                await parser.initialize()
        
        return self._parsers[language]
    
    def _detect_language_from_extension(self, file_path: str) -> str:
        """Detect programming language from file extension.
        
        Args:
            file_path: File path with extension
            
        Returns:
            Detected language name, or default if unknown
        """
        extension_map = {
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.py': 'python',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
        }
        
        import os
        _, ext = os.path.splitext(file_path)
        return extension_map.get(ext.lower(), self._default_language)
    
    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages.
        
        Returns:
            List of language names
        """
        return self._factory.get_supported_languages()


def get_parser_service(
    default_language: str = "typescript",
    project_root: Path | None = None,
    cache_enabled: bool = True
) -> ParserService:
    """Factory function to create parser service.
    
    Args:
        default_language: Default programming language
        project_root: Optional project root directory
        cache_enabled: Whether to enable caching
        
    Returns:
        A configured parser service instance
    """
    config = {
        "default_language": default_language,
        "cache_enabled": cache_enabled
    }
    if project_root:
        config["project_root"] = project_root
    
    return ParserService(config=config)