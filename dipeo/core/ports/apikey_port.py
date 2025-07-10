"""Port interface for API key storage operations."""

from typing import Protocol, Dict, List


class APIKeyStoragePort(Protocol):
    """Port interface for persisting and retrieving API keys."""
    
    async def load_all(self) -> Dict[str, Dict]:
        """Load all API keys from storage.
        
        Returns:
            Dictionary mapping key IDs to key information
        """
        ...
    
    async def save_all(self, store: Dict[str, Dict]) -> None:
        """Save all API keys to storage.
        
        Args:
            store: Dictionary mapping key IDs to key information
        """
        ...
    
    async def exists(self) -> bool:
        """Check if the storage exists.
        
        Returns:
            True if storage exists, False otherwise
        """
        ...