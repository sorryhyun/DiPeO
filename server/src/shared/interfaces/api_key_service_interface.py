"""Interface for API key service."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IAPIKeyService(ABC):
    """Interface for managing API keys."""
    
    @abstractmethod
    def get_api_key(self, key_id: str) -> dict:
        """Get API key details by ID."""
        pass
    
    @abstractmethod
    def list_api_keys(self) -> List[dict]:
        """List all stored API keys."""
        pass
    
    @abstractmethod
    def create_api_key(self, label: str, service: str, key: str) -> dict:
        """Create a new API key entry."""
        pass
    
    @abstractmethod
    def delete_api_key(self, key_id: str) -> None:
        """Delete an API key by ID."""
        pass
    
    @abstractmethod
    def update_api_key(self, key_id: str, label: Optional[str] = None,
                      service: Optional[str] = None, key: Optional[str] = None) -> dict:
        """Update an existing API key."""
        pass