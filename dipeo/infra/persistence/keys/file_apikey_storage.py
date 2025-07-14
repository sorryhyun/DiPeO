"""File-based implementation of API key storage."""

import json
import logging
from pathlib import Path

from dipeo.core.ports.apikey_port import APIKeyPort

log = logging.getLogger(__name__)


class FileAPIKeyStorage(APIKeyPort):
    """File-based storage for API keys implementing APIKeyPort."""
    
    def __init__(self, file_path: Path):
        """Initialize file-based storage.
        
        Args:
            file_path: Path to the JSON file for storing API keys
        """
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def load_all(self) -> dict[str, dict]:
        """Load all API keys from file storage.
        
        Returns:
            Dictionary mapping key IDs to key information
        """
        if not self.file_path.exists():
            return {}
        
        try:
            with open(self.file_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.error(f"Failed to load API keys from {self.file_path}: {e}")
            return {}
    
    async def save_all(self, store: dict[str, dict]) -> None:
        """Save all API keys to file storage.
        
        Args:
            store: Dictionary mapping key IDs to key information
        """
        try:
            with open(self.file_path, 'w') as f:
                json.dump(store, f, indent=2)
        except OSError as e:
            log.error(f"Failed to save API keys to {self.file_path}: {e}")
            raise
    
    async def exists(self) -> bool:
        """Check if the storage file exists.
        
        Returns:
            True if storage exists, False otherwise
        """
        return self.file_path.exists()