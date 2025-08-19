"""Parser configuration module using unified config system."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dipeo.config import get_settings


@dataclass
class ParserConfig:
    """Configuration for language-specific parsers."""
    
    language: str
    project_root: Path
    cache_enabled: bool = True
    script_path: Optional[Path] = None
    
    @classmethod
    def from_env(cls, language: str) -> "ParserConfig":
        """Create parser configuration from environment variables.
        
        Args:
            language: The programming language for the parser
            
        Returns:
            ParserConfig instance with environment-based settings
        """
        settings = get_settings()
        return cls(
            language=language,
            project_root=Path(settings.storage.base_dir),
            cache_enabled=os.getenv('DIPEO_PARSER_CACHE', 'true').lower() == 'true'
        )
    
    @classmethod
    def from_dict(cls, config: dict, language: str) -> "ParserConfig":
        """Create parser configuration from dictionary.
        
        Args:
            config: Configuration dictionary
            language: The programming language for the parser
            
        Returns:
            ParserConfig instance
        """
        settings = get_settings()
        return cls(
            language=language,
            project_root=Path(config.get('project_root', settings.storage.base_dir)),
            cache_enabled=config.get('cache_enabled', True),
            script_path=Path(config['script_path']) if 'script_path' in config else None
        )