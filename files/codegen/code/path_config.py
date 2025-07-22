"""Path configuration loader for codegen system."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class PathConfig:
    """Centralized path configuration for codegen system."""
    
    _instance: Optional['PathConfig'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from paths.json."""
        config_path = Path("files/codegen/paths.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Path configuration not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = json.load(f)
    
    def get_path(self, *keys: str, **kwargs) -> str:
        """
        Get a path from the configuration.
        
        Args:
            *keys: Nested keys to traverse the config (e.g., 'output_paths', 'models', 'typescript')
            **kwargs: Template variables to replace in the path
        
        Returns:
            The resolved path string
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Path not found: {'.'.join(keys)}")
        
        if not isinstance(current, str):
            raise ValueError(f"Expected string path, got: {type(current)}")
        
        # Replace template variables
        path = current
        for key, value in kwargs.items():
            # Handle nested dictionary values (like spec_data.nodeType)
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    path = path.replace(f"{{{{{key}.{nested_key}}}}}", str(nested_value))
            else:
                path = path.replace(f"{{{{{key}}}}}", str(value))
        
        return path
    
    def get_template_path(self, template_name: str) -> str:
        """Get path to a template file."""
        return self.get_path('template_files', template_name)
    
    def get_output_path(self, category: str, subcategory: str, **kwargs) -> str:
        """Get an output path with template variables replaced."""
        return self.get_path('output_paths', category, subcategory, **kwargs)
    
    def get_code_file(self, file_key: str) -> str:
        """Get path to a code file."""
        return self.get_path('code_files', file_key)
    
    def get_schema_file(self, schema_key: str) -> str:
        """Get path to a schema file."""
        return self.get_path('schema_files', schema_key)
    
    def get_source_path(self, source_key: str) -> str:
        """Get a source path."""
        return self.get_path('source_paths', source_key)
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config.copy()


# Convenience functions
def get_path_config() -> PathConfig:
    """Get the singleton PathConfig instance."""
    return PathConfig()


def resolve_path(*keys: str, **kwargs) -> str:
    """Shorthand for getting a path from config."""
    return get_path_config().get_path(*keys, **kwargs)


def resolve_template_path(template_name: str) -> str:
    """Shorthand for getting a template path."""
    return get_path_config().get_template_path(template_name)


def resolve_output_path(category: str, subcategory: str, **kwargs) -> str:
    """Shorthand for getting an output path."""
    return get_path_config().get_output_path(category, subcategory, **kwargs)