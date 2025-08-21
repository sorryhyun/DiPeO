"""Base protocol for template engine adapters."""

from typing import Protocol, Any, Dict, Optional, Callable
from abc import abstractmethod


class TemplateEngineAdapter(Protocol):
    """Protocol for template engine adapters.
    
    This defines the interface that all template engines must implement.
    Adapters are responsible for low-level template rendering operations.
    """
    
    @abstractmethod
    async def render(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a template file with given context.
        
        Args:
            template_path: Path to the template file
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered template string
        """
        ...
    
    @abstractmethod
    async def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with given context.
        
        Args:
            template_str: Template string to render
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered template string
        """
        ...
    
    @abstractmethod
    def register_filter(self, name: str, filter_func: Callable) -> None:
        """Register a custom filter.
        
        Args:
            name: Name of the filter
            filter_func: Filter function to register
        """
        ...
    
    @abstractmethod
    def register_macro(self, name: str, macro_def: str) -> None:
        """Register a macro.
        
        Args:
            name: Name of the macro
            macro_def: Macro definition
        """
        ...
    
    @abstractmethod
    def add_template_directory(self, directory: str) -> None:
        """Add a directory to the template search path.
        
        Args:
            directory: Directory path to add
        """
        ...
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any template caches."""
        ...