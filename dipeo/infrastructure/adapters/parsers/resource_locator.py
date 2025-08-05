"""Resource locator for parser scripts and resources."""

from pathlib import Path
from typing import Optional


class ParserResourceLocator:
    """Locates parser scripts and resources for different languages."""
    
    # Mapping of language to relative script paths
    PARSER_SCRIPTS = {
        "typescript": "typescript/ts_parser_main.ts",  # Refactored modular parser
        "python": "python/py_ast_extractor.py",
        "javascript": "typescript/ts_parser_main.ts",  # Reuse TypeScript parser
        "rust": "rust/rust_ast_extractor.rs",
        "go": "go/go_ast_extractor.go",
    }
    
    @classmethod
    def get_parser_script(cls, language: str, base_dir: Path) -> Path:
        """Get the parser script path for a specific language.
        
        Args:
            language: The programming language
            base_dir: The base directory (usually DIPEO_BASE_DIR)
            
        Returns:
            Full path to the parser script
            
        Raises:
            ValueError: If no parser script exists for the language
        """
        script_rel_path = cls.PARSER_SCRIPTS.get(language.lower())
        if not script_rel_path:
            raise ValueError(f"No parser script configured for language: {language}")
            
        return base_dir / 'dipeo/infrastructure/adapters/parsers' / script_rel_path
    
    @classmethod
    def is_supported(cls, language: str) -> bool:
        """Check if a language is supported.
        
        Args:
            language: The programming language
            
        Returns:
            True if the language has a parser script configured
        """
        return language.lower() in cls.PARSER_SCRIPTS
    
    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get list of supported languages.
        
        Returns:
            List of language names that have parser scripts
        """
        return list(cls.PARSER_SCRIPTS.keys())
    
    @classmethod
    def register_parser_script(cls, language: str, script_path: str) -> None:
        """Register a new parser script for a language (runtime registration).
        
        Args:
            language: The programming language
            script_path: Relative path to the parser script
        """
        cls.PARSER_SCRIPTS[language.lower()] = script_path