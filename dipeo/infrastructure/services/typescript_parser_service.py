"""TypeScript parser service for dependency injection."""

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.core import BaseService
from dipeo.core.ports.ast_parser_port import ASTParserPort
from dipeo.infrastructure.adapters.parsers.typescript.parser import TypeScriptParser

logger = logging.getLogger(__name__)


class TypeScriptParserService(BaseService, ASTParserPort):
    """TypeScript parser service implementing the AST parser port.
    
    This service provides a consistent interface for TypeScript parsing
    that follows the standard service patterns with proper lifecycle management.
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the TypeScript parser service.
        
        Args:
            config: Optional configuration dict. Can contain:
                - project_root: Project root directory path
                - cache_enabled: Whether to enable AST caching (default: True)
                - log_level: Logging level for parser operations
        """
        super().__init__(config)
        self._parser: TypeScriptParser | None = None
        self._project_root: Path | None = None
        self._cache_enabled = self.get_config_value("cache_enabled", True)
        
        # Extract project root from config
        if config and "project_root" in config:
            self._project_root = Path(config["project_root"])
        else:
            # Fallback to DIPEO_BASE_DIR or cwd
            self._project_root = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    async def initialize(self) -> None:
        """Initialize the service and create the parser instance.
        
        This method is called during service startup and ensures
        the parser is properly configured and ready to use.
        """
        if not self._parser:
            logger.debug(f"Initializing TypeScript parser with root: {self._project_root}")
            self._parser = TypeScriptParser(project_root=self._project_root)
            
            # Disable cache if configured
            if not self._cache_enabled:
                logger.info("TypeScript parser cache disabled by configuration")
                self._parser.clear_cache()
    
    async def parse(
        self,
        source: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse TypeScript source code and extract AST information.
        
        Args:
            source: The TypeScript source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options
                
        Returns:
            Dictionary containing AST data and metadata
        """
        if not self._parser:
            await self.initialize()
        
        logger.debug(f"Parsing TypeScript source with patterns: {extract_patterns}")
        
        try:
            assert self._parser is not None  # Type hint for mypy
            result = await self._parser.parse(source, extract_patterns, options)
            
            # Log parsing statistics
            if result.get("metadata", {}).get("success"):
                ast_summary = result.get("metadata", {}).get("astSummary", {})
                logger.debug(f"Successfully parsed TypeScript: {ast_summary}")
            
            return result
            
        except Exception as e:
            logger.error(f"TypeScript parsing failed: {e}")
            raise
    
    async def parse_file(
        self,
        file_path: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse a TypeScript file.
        
        Args:
            file_path: Path to the TypeScript file (relative to project root)
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Same as parse() method
        """
        if not self._parser:
            await self.initialize()
        
        logger.debug(f"Parsing TypeScript file: {file_path}")
        assert self._parser is not None  # Type hint for mypy
        return await self._parser.parse_file(file_path, extract_patterns, options)
    
    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript sources in a single operation.
        
        Args:
            sources: Dictionary mapping keys to TypeScript source code
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping each key to its parse result
        """
        if not self._parser:
            await self.initialize()
        
        logger.debug(f"Batch parsing {len(sources)} TypeScript sources")
        assert self._parser is not None  # Type hint for mypy
        result = await self._parser.parse_batch(sources, extract_patterns, options)
        
        # Log batch statistics
        success_count = sum(1 for r in result.values() if r.get("metadata", {}).get("success"))
        logger.debug(f"Batch parsing completed: {success_count}/{len(sources)} successful")
        
        return result
    
    async def parse_files_batch(
        self,
        file_paths: list[str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript files in a single operation.
        
        Args:
            file_paths: List of file paths relative to project root
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping file paths to parse results
        """
        if not self._parser:
            await self.initialize()
        
        logger.debug(f"Batch parsing {len(file_paths)} TypeScript files")
        assert self._parser is not None  # Type hint for mypy
        return await self._parser.parse_files_batch(file_paths, extract_patterns, options)
    
    def clear_cache(self):
        """Clear the parser's AST cache.
        
        This can be useful to free memory or force re-parsing of files.
        """
        if self._parser:
            self._parser.clear_cache()
            logger.info("TypeScript parser cache cleared")


def get_typescript_parser_service(project_root: Path | None = None) -> TypeScriptParserService:
    """Factory function to create TypeScript parser service.
    
    Args:
        project_root: Optional project root directory.
        
    Returns:
        A configured TypeScript parser service instance.
    """
    config = {}
    if project_root:
        config["project_root"] = project_root
    
    return TypeScriptParserService(config=config)