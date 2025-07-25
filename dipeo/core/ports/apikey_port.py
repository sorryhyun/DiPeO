"""Port interface for API key storage operations."""

from typing import Protocol, runtime_checkable


class APIKeyPort(Protocol):
    """Port interface for persisting and retrieving API keys."""

    async def load_all(self) -> dict[str, dict]:
        """Load all API keys from storage.

        Returns:
            Dictionary mapping key IDs to key information
        """
        ...

    async def save_all(self, store: dict[str, dict]) -> None:
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

@runtime_checkable
class SupportsAPIKey(Protocol):
    """Protocol for API key management operations."""

    def get_api_key(self, key_id: str) -> dict: 
        ...
        
    def list_api_keys(self) -> list[dict]: 
        ...
        
    def create_api_key(self, label: str, service: str, key: str) -> dict: 
        ...
        
    def delete_api_key(self, key_id: str) -> None: 
        ...
        
    def update_api_key(
        self,
        key_id: str,
        label: str | None = None,
        service: str | None = None,
        key: str | None = None,
    ) -> dict: 
        ...

