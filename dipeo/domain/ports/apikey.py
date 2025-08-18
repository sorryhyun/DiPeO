"""API Key management port for secure credential storage."""

from typing import Protocol


class APIKeyPort(Protocol):
    """Protocol for API key management."""
    
    async def get_api_key(self, key_name: str) -> str | None:
        """Get an API key by name."""
        ...
    
    async def set_api_key(self, key_name: str, key_value: str) -> None:
        """Set an API key."""
        ...
    
    async def delete_api_key(self, key_name: str) -> None:
        """Delete an API key."""
        ...
    
    async def list_api_keys(self) -> list[str]:
        """List all API key names."""
        ...