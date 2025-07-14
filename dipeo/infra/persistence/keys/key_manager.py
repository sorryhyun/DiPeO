"""API Key Manager for managing credentials and API keys."""

import os
from typing import Dict, Optional
from pathlib import Path

from dipeo.core.base.exceptions import APIKeyError
from .file_apikey_storage import FileAPIKeyStorage


class KeyManager:
    
    def __init__(self, storage: Optional[FileAPIKeyStorage] = None):
        self.storage = storage or FileAPIKeyStorage()
        self._env_cache: Dict[str, str] = {}
        self._load_env_keys()
    
    def _load_env_keys(self) -> None:
        env_mappings = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "notion": "NOTION_API_KEY",
            "azure": "AZURE_API_KEY",
            "cohere": "COHERE_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
        }
        
        for provider, env_var in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._env_cache[provider] = value
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for a specific provider.
        
        This method checks multiple sources in order:
        1. Environment variables (highest priority)
        2. Secure storage
        3. Provider-specific fallbacks
        
        Args:
            provider: The provider name (e.g., 'openai', 'anthropic')
            
        Returns:
            The API key for the provider
            
        Raises:
            APIKeyError: If no API key is found for the provider
        """
        provider = provider.lower()
        
        # Check environment cache first
        if provider in self._env_cache:
            return self._env_cache[provider]
        
        # Check environment variables with common patterns
        env_patterns = [
            f"{provider.upper()}_API_KEY",
            f"{provider.upper()}_KEY",
            f"{provider.upper()}_TOKEN",
        ]
        
        for pattern in env_patterns:
            value = os.getenv(pattern)
            if value:
                self._env_cache[provider] = value
                return value
        
        # Check storage (synchronous wrapper for async storage)
        # In a real implementation, this would need proper async handling
        # For now, we'll raise an error if not found in environment
        raise APIKeyError(
            f"No API key found for provider '{provider}'. "
            f"Please set the {provider.upper()}_API_KEY environment variable."
        )
    
    async def get_api_key_async(self, provider: str) -> str:
        """Async version of get_api_key that can check storage.
        
        Args:
            provider: The provider name
            
        Returns:
            The API key for the provider
            
        Raises:
            APIKeyError: If no API key is found
        """
        provider = provider.lower()
        
        # Check environment cache first
        if provider in self._env_cache:
            return self._env_cache[provider]
        
        # Check storage
        try:
            store = await self.storage.load_all()
            if provider in store:
                key_info = store[provider]
                if isinstance(key_info, dict) and "key" in key_info:
                    return key_info["key"]
                elif isinstance(key_info, str):
                    return key_info
        except Exception:
            # Storage might not be available
            pass
        
        # Fall back to synchronous method
        return self.get_api_key(provider)
    
    async def set_api_key(self, provider: str, key: str) -> None:
        """Store an API key for a provider.
        
        Args:
            provider: The provider name
            key: The API key to store
            
        Raises:
            APIKeyError: If key cannot be stored
        """
        provider = provider.lower()
        
        # Update cache
        self._env_cache[provider] = key
        
        # Store persistently
        store = await self.storage.load_all()
        store[provider] = {
            "key": key,
            "provider": provider,
        }
        await self.storage.save_all(store)
    
    async def remove_api_key(self, provider: str) -> bool:
        """Remove an API key for a provider.
        
        Args:
            provider: The provider name
            
        Returns:
            True if removed, False if not found
        """
        provider = provider.lower()
        
        # Remove from cache
        removed = provider in self._env_cache
        self._env_cache.pop(provider, None)
        
        # Remove from storage
        try:
            store = await self.storage.load_all()
            if provider in store:
                del store[provider]
                await self.storage.save_all(store)
                removed = True
        except Exception:
            pass
        
        return removed
    
    async def list_providers(self) -> list[str]:
        """List all providers with available API keys.
        
        Returns:
            List of provider names
        """
        providers = set(self._env_cache.keys())
        
        # Add providers from storage
        try:
            store = await self.storage.load_all()
            providers.update(store.keys())
        except Exception:
            pass
        
        return sorted(list(providers))
    
    def has_api_key(self, provider: str) -> bool:
        """Check if an API key exists for a provider.
        
        Args:
            provider: The provider name
            
        Returns:
            True if API key exists, False otherwise
        """
        provider = provider.lower()
        
        # Check cache
        if provider in self._env_cache:
            return True
        
        # Check environment with patterns
        env_patterns = [
            f"{provider.upper()}_API_KEY",
            f"{provider.upper()}_KEY",
            f"{provider.upper()}_TOKEN",
        ]
        
        for pattern in env_patterns:
            if os.getenv(pattern):
                return True
        
        return False