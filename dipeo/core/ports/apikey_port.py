"""Port interface for API key management operations."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class APIKeyPort(Protocol):
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

