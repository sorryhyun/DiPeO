"""Filter registry for managing and composing template filters.

This module provides a registry system for template filters, allowing:
- Dynamic registration of filter collections
- Composition of multiple filter sets
- Filter discovery and documentation
"""

from typing import Dict, Callable, Any, Set, Optional, List
from dataclasses import dataclass, field


@dataclass
class FilterInfo:
    """Information about a registered filter."""
    name: str
    function: Callable
    source: str  # e.g., 'base', 'typescript', 'graphql'
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)


class FilterRegistry:
    """Registry for managing template filters."""
    
    def __init__(self):
        self._filters: Dict[str, FilterInfo] = {}
        self._sources: Dict[str, Set[str]] = {}  # source -> filter names
        
    def register_filter(
        self, 
        name: str, 
        function: Callable,
        source: str,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None
    ) -> None:
        """Register a single filter.
        
        Args:
            name: Filter name
            function: Filter function
            source: Source identifier (e.g., 'base', 'typescript')
            description: Optional description
            aliases: Optional list of alternative names
        """
        filter_info = FilterInfo(
            name=name,
            function=function,
            source=source,
            description=description,
            aliases=aliases or []
        )
        
        # Register main name
        self._filters[name] = filter_info
        
        # Register aliases
        for alias in filter_info.aliases:
            self._filters[alias] = filter_info
            
        # Track by source
        if source not in self._sources:
            self._sources[source] = set()
        self._sources[source].add(name)
        
    def register_filter_collection(self, source: str, filters: Dict[str, Callable]) -> None:
        """Register a collection of filters from a single source.
        
        Args:
            source: Source identifier
            filters: Dictionary of filter name -> function
        """
        for name, function in filters.items():
            self.register_filter(name, function, source)
            
    def get_filter(self, name: str) -> Optional[Callable]:
        """Get a filter function by name."""
        filter_info = self._filters.get(name)
        return filter_info.function if filter_info else None
        
    def get_filters_by_source(self, source: str) -> Dict[str, Callable]:
        """Get all filters from a specific source."""
        filter_names = self._sources.get(source, set())
        return {
            name: self._filters[name].function 
            for name in filter_names 
            if name in self._filters
        }
        
    def get_all_filters(self) -> Dict[str, Callable]:
        """Get all registered filters."""
        # Return unique filters (avoiding duplicates from aliases)
        seen_functions = set()
        result = {}
        
        for name, filter_info in self._filters.items():
            if filter_info.function not in seen_functions:
                result[name] = filter_info.function
                seen_functions.add(filter_info.function)
                
        return result
        
    def compose_filters(self, *sources: str) -> Dict[str, Callable]:
        """Compose filters from multiple sources.
        
        Args:
            *sources: Source identifiers to include
            
        Returns:
            Dictionary of all filters from specified sources
        """
        result = {}
        for source in sources:
            result.update(self.get_filters_by_source(source))
        return result
        
    def get_filter_info(self, name: str) -> Optional[FilterInfo]:
        """Get detailed information about a filter."""
        return self._filters.get(name)
        
    def list_sources(self) -> List[str]:
        """List all registered filter sources."""
        return list(self._sources.keys())
        
    def list_filters(self, source: Optional[str] = None) -> List[str]:
        """List filter names, optionally filtered by source."""
        if source:
            return list(self._sources.get(source, []))
        else:
            # Return unique filter names (excluding aliases)
            seen_functions = set()
            result = []
            
            for name, filter_info in self._filters.items():
                if filter_info.function not in seen_functions:
                    result.append(name)
                    seen_functions.add(filter_info.function)
                    
            return sorted(result)


# Global registry instance
filter_registry = FilterRegistry()


def create_filter_registry() -> FilterRegistry:
    """Create a new filter registry with default filters loaded."""
    registry = FilterRegistry()
    
    # Import and register default filter collections
    try:
        from .base_filters import BaseFilters
        registry.register_filter_collection('base', BaseFilters.get_all_filters())
    except ImportError:
        pass
        
    try:
        from .typescript_filters import TypeScriptToPythonFilters
        registry.register_filter_collection('typescript', TypeScriptToPythonFilters.get_all_filters())
    except ImportError:
        pass
        
    return registry