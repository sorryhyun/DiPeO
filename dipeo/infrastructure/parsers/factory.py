"""Parser factory for creating language-specific parsers."""

from typing import Any, Optional

from dipeo.domain.base.exceptions import ServiceError
from dipeo.domain.ports.parsers import ASTParserPort
from dipeo.infrastructure.config.parser_config import ParserConfig

from .registry import ParserRegistry
from .resource_locator import ParserResourceLocator
from .typescript.parser import TypeScriptParser


class ParserFactory:
    """Factory for creating language-specific AST parsers."""
    
    # Registry for custom parser implementations
    _custom_parsers: dict[str, type[ASTParserPort]] = {}
    
    @classmethod
    def create_parser(cls, config: ParserConfig) -> ASTParserPort:
        """Create a parser instance based on configuration.
        
        Args:
            config: Parser configuration with language and settings
            
        Returns:
            An AST parser instance for the specified language
            
        Raises:
            ServiceError: If the language is not supported
        """
        language = config.language.lower()
        
        # Check ParserRegistry first (highest priority)
        registry_class = ParserRegistry.get_parser_class(language)
        if registry_class:
            return registry_class(config)
        
        registry_factory = ParserRegistry.get_parser_factory(language)
        if registry_factory:
            return registry_factory(config)
        
        # Check for custom registered parser (backward compatibility)
        if language in cls._custom_parsers:
            parser_class = cls._custom_parsers[language]
            return parser_class(config)
        
        # Built-in parsers
        if language in ("typescript", "javascript"):
            script_path = config.script_path or ParserResourceLocator.get_parser_script(
                config.language, config.project_root
            )
            return TypeScriptParser(
                project_root=config.project_root,
                parser_script=script_path,
                cache_enabled=config.cache_enabled
            )
        
        # Future parsers can be added here
        # elif language == "python":
        #     return PythonParser(config)
        # elif language == "rust":
        #     return RustParser(config)
        
        raise ServiceError(
            f"Unsupported language: {config.language}. "
            f"Supported languages: {cls.get_supported_languages()}"
        )
    
    @classmethod
    def register_parser(cls, language: str, parser_class: type[ASTParserPort]) -> None:
        """Register a custom parser implementation for a language.
        
        Args:
            language: The programming language
            parser_class: The parser class implementing ASTParserPort
        """
        cls._custom_parsers[language.lower()] = parser_class
    
    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get list of all supported languages.
        
        Returns:
            List of language names that have parser implementations
        """
        built_in = ["typescript", "javascript"]
        custom = list(cls._custom_parsers.keys())
        registry = ParserRegistry.get_registered_languages()
        return sorted(set(built_in + custom + registry))