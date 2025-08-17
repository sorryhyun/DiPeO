"""Parser registry for dynamic registration of language parsers."""

import logging
from typing import Any, Callable, Dict, Type

from dipeo.domain.parsers.ports import ASTParserPort

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Registry for dynamically registering parser implementations.
    
    This allows runtime registration of new parser implementations,
    enabling plugin-based architecture for language support.
    """
    
    # Class-level storage for registered parsers
    _parsers: Dict[str, Type[ASTParserPort]] = {}
    _parser_factories: Dict[str, Callable[[Any], ASTParserPort]] = {}
    
    @classmethod
    def register_parser_class(cls, language: str, parser_class: Type[ASTParserPort]) -> None:
        """Register a parser class for a language.
        
        Args:
            language: The programming language (e.g., "python", "rust")
            parser_class: The parser class implementing ASTParserPort
        """
        cls._parsers[language.lower()] = parser_class
        logger.info(f"Registered parser class for {language}: {parser_class.__name__}")
    
    @classmethod
    def register_parser_factory(cls, language: str, factory: Callable[[Any], ASTParserPort]) -> None:
        """Register a parser factory function for a language.
        
        Args:
            language: The programming language
            factory: A callable that creates parser instances
        """
        cls._parser_factories[language.lower()] = factory
        logger.info(f"Registered parser factory for {language}")
    
    @classmethod
    def get_parser_class(cls, language: str) -> Type[ASTParserPort] | None:
        """Get the registered parser class for a language.
        
        Args:
            language: The programming language
            
        Returns:
            Parser class if registered, None otherwise
        """
        return cls._parsers.get(language.lower())
    
    @classmethod
    def get_parser_factory(cls, language: str) -> Callable[[Any], ASTParserPort] | None:
        """Get the registered parser factory for a language.
        
        Args:
            language: The programming language
            
        Returns:
            Parser factory if registered, None otherwise
        """
        return cls._parser_factories.get(language.lower())
    
    @classmethod
    def is_registered(cls, language: str) -> bool:
        """Check if a parser is registered for a language.
        
        Args:
            language: The programming language
            
        Returns:
            True if a parser is registered for the language
        """
        lang_lower = language.lower()
        return lang_lower in cls._parsers or lang_lower in cls._parser_factories
    
    @classmethod
    def get_registered_languages(cls) -> list[str]:
        """Get list of all registered languages.
        
        Returns:
            List of language names with registered parsers
        """
        languages = set(cls._parsers.keys()) | set(cls._parser_factories.keys())
        return sorted(languages)
    
    @classmethod
    def unregister(cls, language: str) -> None:
        """Unregister a parser for a language.
        
        Args:
            language: The programming language
        """
        lang_lower = language.lower()
        removed = False
        
        if lang_lower in cls._parsers:
            del cls._parsers[lang_lower]
            removed = True
        
        if lang_lower in cls._parser_factories:
            del cls._parser_factories[lang_lower]
            removed = True
        
        if removed:
            logger.info(f"Unregistered parser for {language}")
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers."""
        cls._parsers.clear()
        cls._parser_factories.clear()
        logger.info("Cleared all registered parsers")


def parser_plugin(language: str):
    """Decorator for registering parser classes.
    
    Usage:
        @parser_plugin("python")
        class PythonParser(ASTParserPort):
            ...
    
    Args:
        language: The programming language the parser supports
    """
    def decorator(parser_class: Type[ASTParserPort]):
        ParserRegistry.register_parser_class(language, parser_class)
        return parser_class
    return decorator