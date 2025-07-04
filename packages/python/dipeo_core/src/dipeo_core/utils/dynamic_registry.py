"""Generic dynamic registry pattern for service management."""

from typing import Any, Dict, Optional, Set, Type, TypeVar

T = TypeVar('T')


class DynamicRegistry:
    """Base class for creating registries with dynamic attribute resolution.
    
    This pattern eliminates the need for manual property definitions when exposing
    services or components through a registry interface.
    
    Example usage:
        class MyServiceRegistry(DynamicRegistry):
            def __init__(self, db_service, cache_service):
                super().__init__()
                self.register("db", db_service)
                self.register("cache", cache_service)
        
        registry = MyServiceRegistry(db, cache)
        registry.db  # Access service via dynamic attribute
    """
    
    def __init__(self):
        """Initialize the dynamic registry."""
        self._items: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
        self._reserved_attrs: Set[str] = {
            '_items', '_aliases', '_reserved_attrs', 
            'register', 'unregister', 'get', 'has', 
            'list_items', 'create_alias', '__getattr__',
            '__setattr__', '__delattr__', '__dir__'
        }
    
    def register(self, name: str, item: Any, aliases: Optional[list[str]] = None) -> None:
        """Register an item in the registry.
        
        Args:
            name: Primary name for the item
            item: The item to register
            aliases: Optional list of alternative names
        """
        if name in self._reserved_attrs:
            raise ValueError(f"Cannot register reserved attribute name: {name}")
        
        self._items[name] = item
        
        if aliases:
            for alias in aliases:
                if alias in self._reserved_attrs:
                    raise ValueError(f"Cannot use reserved name as alias: {alias}")
                self._aliases[alias] = name
    
    def unregister(self, name: str) -> Any:
        """Remove an item from the registry.
        
        Args:
            name: Name of the item to remove
            
        Returns:
            The removed item
        """
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
        """Get an item from the registry.
        
        Args:
            name: Name of the item
            default: Default value if not found
            
        Returns:
            The item or default value
        """
        # Check direct name first
        if name in self._items:
            return self._items[name]
        
        # Check aliases
        if name in self._aliases:
            return self._items.get(self._aliases[name], default)
        
        return default
    
    def has(self, name: str) -> bool:
        """Check if an item exists in the registry.
        
        Args:
            name: Name to check
            
        Returns:
            True if the item exists
        """
        return name in self._items or name in self._aliases
    
    def create_alias(self, alias: str, target: str) -> None:
        """Create an alias for an existing item.
        
        Args:
            alias: New alias name
            target: Existing item name
        """
        if alias in self._reserved_attrs:
            raise ValueError(f"Cannot use reserved name as alias: {alias}")
        
        if target not in self._items:
            raise KeyError(f"Target item not found: {target}")
        
        self._aliases[alias] = target
    
    def list_items(self) -> Dict[str, str]:
        """List all registered items and their aliases.
        
        Returns:
            Dictionary mapping names to descriptions
        """
        result = {}
        
        # Add primary names
        for name in self._items:
            result[name] = "Primary"
        
        # Add aliases
        for alias, target in self._aliases.items():
            result[alias] = f"Alias for '{target}'"
        
        return result
    
    def __getattr__(self, name: str) -> Any:
        """Dynamic attribute access for registered items."""
        item = self.get(name)
        if item is not None:
            return item
        
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Handle attribute setting."""
        if name in self._reserved_attrs or name.startswith('_'):
            # Use default behavior for reserved/private attributes
            super().__setattr__(name, value)
        else:
            # Register as a new item
            self.register(name, value)
    
    def __delattr__(self, name: str) -> None:
        """Handle attribute deletion."""
        if self.has(name):
            self.unregister(name)
        else:
            super().__delattr__(name)
    
    def __dir__(self) -> list[str]:
        """List available attributes including dynamic ones."""
        base_attrs = list(super().__dir__())
        dynamic_attrs = list(self._items.keys()) + list(self._aliases.keys())
        return sorted(set(base_attrs + dynamic_attrs))


class TypedDynamicRegistry(DynamicRegistry):
    """Type-safe version of DynamicRegistry that enforces item types.
    
    Example usage:
        class ServiceRegistry(TypedDynamicRegistry[BaseService]):
            item_type = BaseService
        
        registry = ServiceRegistry()
        registry.register("db", DBService())  # Must be BaseService subclass
    """
    
    item_type: Type[T] = object  # Override in subclasses
    
    def register(self, name: str, item: T, aliases: Optional[list[str]] = None) -> None:
        """Register an item with type checking."""
        if not isinstance(item, self.item_type):
            raise TypeError(
                f"Item must be instance of {self.item_type.__name__}, "
                f"got {type(item).__name__}"
            )
        super().register(name, item, aliases)