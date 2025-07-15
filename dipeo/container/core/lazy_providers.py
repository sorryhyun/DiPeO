"""Lazy provider implementations for deferred service initialization."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from dependency_injector import providers

T = TypeVar('T')


class LazyAsyncSingleton(providers.Singleton):
    """A singleton provider that defers initialization until first use."""
    
    def __init__(self, factory: Callable[..., Any], *args, **kwargs):
        super().__init__(factory, *args, **kwargs)
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        self._instance: Any | None = None
    
    async def __call__(self, *args, **kwargs) -> T:
        """Get or create the singleton instance with lazy initialization."""
        if not self._initialized:
            async with self._initialization_lock:
                if not self._initialized:  # Double-check pattern
                    # Create instance
                    self._instance = await self._provide(args, kwargs)
                    
                    # Initialize if it has an initialize method
                    if hasattr(self._instance, 'initialize'):
                        await self._instance.initialize()
                    
                    self._initialized = True
        
        return self._instance
    
    def is_initialized(self) -> bool:
        """Check if the service has been initialized."""
        return self._initialized


class ConditionalProvider(providers.Provider):
    """Provider that returns different implementations based on a condition."""
    
    def __init__(self, 
                 condition: Callable[[], bool],
                 when_true: providers.Provider,
                 when_false: providers.Provider | None = None):
        self._condition = condition
        self._when_true = when_true
        self._when_false = when_false or providers.Object(None)
        super().__init__()
    
    def _provide(self, args, kwargs):
        """Provide based on condition."""
        if self._condition():
            return self._when_true(*args, **kwargs)
        else:
            return self._when_false(*args, **kwargs)


class ProfileBasedProvider(providers.Provider):
    """Provider that selects implementation based on container profile."""
    
    def __init__(self, profile_providers: dict[str, providers.Provider]):
        self._profile_providers = profile_providers
        self._current_profile = 'full'  # Default profile
        super().__init__()
    
    def set_profile(self, profile: str) -> None:
        """Set the active profile."""
        if profile not in self._profile_providers:
            raise ValueError(f"Unknown profile: {profile}. Available: {list(self._profile_providers.keys())}")
        self._current_profile = profile
    
    def _provide(self, args, kwargs):
        """Provide based on current profile."""
        provider = self._profile_providers.get(self._current_profile)
        if provider:
            return provider(*args, **kwargs)
        else:
            # Fallback to 'full' profile if available
            return self._profile_providers.get('full', providers.Object(None))(*args, **kwargs)
