"""Generic dynamic registry pattern for service management."""

from typing import Any, Dict, Optional, Set, Type, TypeVar

T = TypeVar('T')


class DynamicRegistry:
    """Registry with dynamic attribute resolution.
    
    Eliminates manual property definitions for service access.
    Usage: registry.service_name to access registered services.
    """
    
    def __init__(self):
        self._items: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
        self._reserved_attrs: Set[str] = {
            '_items', '_aliases', '_reserved_attrs', 
            'register', 'unregister', 'get', 'has', 
            'list_items', 'create_alias', '__getattr__',
            '__setattr__', '__delattr__', '__dir__'
        }
    
    def register(self, name: str, item: Any, aliases: Optional[list[str]] = None) -> None:
        # Register item with optional aliases
        if name in self._reserved_attrs:
            raise ValueError(f"Cannot register reserved attribute name: {name}")
        
        self._items[name] = item
        
        if aliases:
            for alias in aliases:
                if alias in self._reserved_attrs:
                    raise ValueError(f"Cannot use reserved name as alias: {alias}")
                self._aliases[alias] = name
    
    def unregister(self, name: str) -> Any:
        # Remove item and associated aliases
        # Remove the item
        item = self._items.pop(name, None)
        
        # Remove any aliases pointing to this item
        aliases_to_remove = [
            alias for alias, target in self._aliases.items() 
            if target == name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]
        
        return item
    
    def get(self, name: str, default: Any = None) -> Any:
        # Get item by name or alias
        # Use object.__getattribute__ to avoid recursion
        try:
            items = object.__getattribute__(self, '_items')
            aliases = object.__getattribute__(self, '_aliases')
        except AttributeError:
            return default
            
        # Check direct name first
        if name in items:
            return items[name]
        
        # Check aliases
        if name in aliases:
            return items.get(aliases[name], default)
        
        return default
    
    def has(self, name: str) -> bool:
        # Check if item exists
        # Use object.__getattribute__ to avoid recursion
        try:
            items = object.__getattribute__(self, '_items')
            aliases = object.__getattribute__(self, '_aliases')
            return name in items or name in aliases
        except AttributeError:
            return False
    
    def create_alias(self, alias: str, target: str) -> None:
        # Create alias for existing item
        if alias in self._reserved_attrs:
            raise ValueError(f"Cannot use reserved name as alias: {alias}")
        
        if target not in self._items:
            raise KeyError(f"Target item not found: {target}")
        
        self._aliases[alias] = target
    
    def list_items(self) -> Dict[str, str]:
        # List all items and aliases
        result = {}
        
        # Add primary names
        for name in self._items:
            result[name] = "Primary"
        
        # Add aliases
        for alias, target in self._aliases.items():
            result[alias] = f"Alias for '{target}'"
        
        return result
    
    def __getattr__(self, name: str) -> Any:
        item = self.get(name)
        if item is not None:
            return item
        
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )
    
    def __setattr__(self, name: str, value: Any) -> None:
        # Use object.__getattribute__ to avoid recursion
        try:
            reserved_attrs = object.__getattribute__(self, '_reserved_attrs')
        except AttributeError:
            # During initialization, _reserved_attrs doesn't exist yet
            # Allow setting private attributes during init
            if name.startswith('_'):
                super().__setattr__(name, value)
                return
            reserved_attrs = set()
        
        if name in reserved_attrs or name.startswith('_'):
            # Use default behavior for reserved/private attributes
            super().__setattr__(name, value)
        else:
            # Register as a new item
            self.register(name, value)
    
    def __delattr__(self, name: str) -> None:
        if self.has(name):
            self.unregister(name)
        else:
            super().__delattr__(name)
    
    def __dir__(self) -> list[str]:
        base_attrs = list(super().__dir__())
        
        # Use object.__getattribute__ to avoid recursion
        try:
            items = object.__getattribute__(self, '_items')
            aliases = object.__getattribute__(self, '_aliases')
            dynamic_attrs = list(items.keys()) + list(aliases.keys())
        except AttributeError:
            dynamic_attrs = []
        
        return sorted(set(base_attrs + dynamic_attrs))


class TypedDynamicRegistry(DynamicRegistry):
    """Type-safe registry that enforces item types.
    
    Override item_type in subclasses for type safety.
    """
    
    item_type: Type[T] = object  # Override in subclasses
    
    def register(self, name: str, item: T, aliases: Optional[list[str]] = None) -> None:
        # Register with type validation
        if not isinstance(item, self.item_type):
            raise TypeError(
                f"Item must be instance of {self.item_type.__name__}, "
                f"got {type(item).__name__}"
            )
        super().register(name, item, aliases)