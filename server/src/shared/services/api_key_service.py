import json
import os
import uuid
from typing import Dict, List, Optional

from config import BASE_DIR
from ..exceptions.exceptions import APIKeyError, ValidationError
from ..utils.base_service import BaseService
from ..domain import LLMService as LLMServiceEnum

class APIKeyService(BaseService):
    """Service for managing API keys."""
    
    # Include both LLM services and other external services
    VALID_SERVICES = {service.value for service in LLMServiceEnum} | {"notion"}
    
    def __init__(self, store_file: Optional[str] = None):
        super().__init__()
        self.store_file = store_file or os.getenv("API_KEY_STORE_FILE", f"{BASE_DIR}/files/apikeys.json")
        self._store: Dict[str, dict] = {}
        self._load_store()
    
    def _load_store(self) -> None:
        """Load API keys from disk storage."""
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file, "r") as f:
                    self._store.update(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                raise APIKeyError(f"Failed to load API key store: {e}")
    
    def _save_store(self) -> None:
        """Save API keys to disk storage."""
        try:
            with open(self.store_file, "w") as f:
                json.dump(self._store, f, indent=2)
        except IOError as e:
            raise APIKeyError(f"Failed to save API key store: {e}")
    
    def _validate_service(self, service: str) -> None:
        """Validate service name."""
        normalized_service = self.normalize_service_name(service)
        if normalized_service not in self.VALID_SERVICES:
            raise ValidationError(f"Invalid service. Must be one of: {self.VALID_SERVICES}")
    
    def get_api_key(self, key_id: str) -> dict:
        """Get API key details by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        info = self._store[key_id]
        # Ensure the returned format is consistent
        if isinstance(info, dict):
            return {
                "id": key_id,
                "label": info.get("label", key_id),
                "service": info.get("service", "unknown"),
                "key": info.get("key", "")
            }
        return info
    
    def list_api_keys(self) -> List[dict]:
        """List all stored API keys."""
        result = []
        for key_id, info in self._store.items():
            # Handle both old and new format API keys
            if isinstance(info, dict) and "service" in info:
                result.append({
                    "id": key_id,
                    "label": info.get("label", key_id),  # Use key_id as fallback name
                    "service": info["service"]
                })
        return result
    
    def create_api_key(self, label: str, service: str, key: str) -> dict:
        """Create a new API key entry."""
        self.validate_required_fields(
            {"label": label, "service": service, "key": key},
            ["label", "service", "key"]
        )
        
        self._validate_service(service)
        
        key_id = f"APIKEY_{uuid.uuid4().hex[:6].upper()}"
        normalized_service = self.normalize_service_name(service)
        
        self._store[key_id] = {
            "label": label,
            "service": normalized_service,
            "key": key
        }
        
        self._save_store()
        
        return {
            "id": key_id,
            "label": label,
            "service": normalized_service
        }
    
    def delete_api_key(self, key_id: str) -> None:
        """Delete an API key by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        del self._store[key_id]
        self._save_store()
    
    def update_api_key(self, key_id: str, label: Optional[str] = None,
                      service: Optional[str] = None, key: Optional[str] = None) -> dict:
        """Update an existing API key."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        api_key_data = self._store[key_id].copy()
        
        if label is not None:
            api_key_data["label"] = label
        if service is not None:
            self._validate_service(service)
            api_key_data["service"] = self.normalize_service_name(service)
        if key is not None:
            api_key_data["key"] = key
        
        self._store[key_id] = api_key_data
        self._save_store()
        
        return {
            "id": key_id,
            "label": api_key_data["label"],
            "service": api_key_data["service"]
        }