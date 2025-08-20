"""Registry system for managing and composing template filters."""

from typing import Dict, Callable, Any, Set, Optional, List
from dataclasses import dataclass, field


@dataclass
class FilterInfo:
    name: str
    function: Callable
    source: str
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)


class FilterRegistry:
    
    def __init__(self):
        self._filters: Dict[str, FilterInfo] = {}
        self._sources: Dict[str, Set[str]] = {}
        
    def register_filter(
        self, 
        name: str, 
        function: Callable,
        source: str,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None
    ) -> None:
        filter_info = FilterInfo(
            name=name,
            function=function,
            source=source,
            description=description,
            aliases=aliases or []
        )
        
        self._filters[name] = filter_info
        
        for alias in filter_info.aliases:
            self._filters[alias] = filter_info
            
        if source not in self._sources:
            self._sources[source] = set()
        self._sources[source].add(name)
        
    def register_filter_collection(self, source: str, filters: Dict[str, Callable]) -> None:
        for name, function in filters.items():
            self.register_filter(name, function, source)
            
    def get_filter(self, name: str) -> Optional[Callable]:
        filter_info = self._filters.get(name)
        return filter_info.function if filter_info else None
        
    def get_filters_by_source(self, source: str) -> Dict[str, Callable]:
        filter_names = self._sources.get(source, set())
        return {
            name: self._filters[name].function 
            for name in filter_names 
            if name in self._filters
        }
        
    def get_all_filters(self) -> Dict[str, Callable]:
        seen_functions = set()
        result = {}
        
        for name, filter_info in self._filters.items():
            if filter_info.function not in seen_functions:
                result[name] = filter_info.function
                seen_functions.add(filter_info.function)
                
        return result
        
    def compose_filters(self, *sources: str) -> Dict[str, Callable]:
        result = {}
        for source in sources:
            result.update(self.get_filters_by_source(source))
        return result
        
    def get_filter_info(self, name: str) -> Optional[FilterInfo]:
        return self._filters.get(name)
        
    def list_sources(self) -> List[str]:
        return list(self._sources.keys())
        
    def list_filters(self, source: Optional[str] = None) -> List[str]:
        if source:
            return list(self._sources.get(source, []))
        else:
            seen_functions = set()
            result = []
            
            for name, filter_info in self._filters.items():
                if filter_info.function not in seen_functions:
                    result.append(name)
                    seen_functions.add(filter_info.function)
                    
            return sorted(result)


filter_registry = FilterRegistry()


def create_filter_registry() -> FilterRegistry:
    return _create_filter_registry_profile('full')


def create_filter_registry_profile(profile: str = 'full') -> FilterRegistry:
    return _create_filter_registry_profile(profile)


def _create_filter_registry_profile(profile: str) -> FilterRegistry:
    registry = FilterRegistry()
    # Lazy imports keep optional deps optional.
    from .base_filters import BaseFilters
    from .typescript_filters import TypeScriptToPythonFilters
    from .backend_filters import BackendFilters
    from .graphql_filters import TypeScriptToGraphQLFilters

    if profile == 'codegen':
        # Minimal, proven-by-templates set
        base = BaseFilters.get_all_filters()
        ts = TypeScriptToPythonFilters.get_all_filters()
        be = BackendFilters.get_all_filters()
        gql = TypeScriptToGraphQLFilters.get_all_filters()
        
        registry.register_filter_collection('base', {
            'snake_case': base['snake_case'],
            'pascal_case': base['pascal_case'],
            'humanize': base['humanize'],
        })
        registry.register_filter_collection('typescript', {
            'ts_to_python': ts['ts_to_python'],
            'to_py': ts['to_py'],
            'is_optional_ts': ts['is_optional_ts'],
            'typescript_type': ts['typescript_type'],
            'ui_field_type': ts['ui_field_type'],
            'zod_schema': ts['zod_schema'],
            'escape_js': ts['escape_js'],
        })
        registry.register_filter_collection('backend', {
            'python_type_with_context': be['python_type_with_context'],
            'python_default': be['python_default'],
        })
        registry.register_filter_collection('graphql', {
            'graphql_field_type': gql['graphql_field_type'],
        })
        return registry

    # Fallback: previous behavior (register everything)
    registry.register_filter_collection('base', BaseFilters.get_all_filters())
    registry.register_filter_collection('typescript', TypeScriptToPythonFilters.get_all_filters())
    registry.register_filter_collection('backend', BackendFilters.get_all_filters())
    registry.register_filter_collection('graphql', TypeScriptToGraphQLFilters.get_all_filters())
    return registry