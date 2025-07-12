"""API Key orchestration service in the application layer."""

from dipeo.core import BaseService, APIKeyError
from dipeo.application.protocols import SupportsAPIKey
from dipeo.core.ports import APIKeyPort
from dipeo.domain.api.services import (
    validate_service_name,
    validate_api_key_format,
    generate_api_key_id,
    format_api_key_info,
    extract_api_key_summary,
)


class APIKeyService(BaseService, SupportsAPIKey):
    # Orchestrates API key management between business logic and storage
    
    def __init__(self, storage: APIKeyPort):
        super().__init__()
        self.storage = storage
        self._store: dict[str, dict] = {}
    
    async def initialize(self) -> None:
        self._store = await self.storage.load_all()
        print(f"[APIKeyService] Loaded {len(self._store)} keys")
    
    async def _save_store(self) -> None:
        await self.storage.save_all(self._store)
    
    def get_api_key(self, key_id: str) -> dict:
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        info = self._store[key_id]
        return format_api_key_info(key_id, info)
    
    def list_api_keys(self) -> list[dict]:
        result = []
        for key_id, info in self._store.items():
            summary = extract_api_key_summary(key_id, info)
            if summary:
                result.append(summary)
        return result
    
    async def create_api_key(self, label: str, service: str, key: str) -> dict:
        self.validate_required_fields(
            {"label": label, "service": service, "key": key},
            ["label", "service", "key"],
        )
        
        # Validate service name
        normalized_service = validate_service_name(service)
        
        # Validate API key format
        validate_api_key_format(key, normalized_service)
        
        # Generate unique ID
        key_id = generate_api_key_id()
        
        # Store the API key
        self._store[key_id] = {
            "label": label,
            "service": normalized_service,
            "key": key,
        }
        
        await self._save_store()
        
        return {"id": key_id, "label": label, "service": normalized_service}
    
    async def delete_api_key(self, key_id: str) -> None:
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        del self._store[key_id]
        await self._save_store()
    
    async def update_api_key(
        self,
        key_id: str,
        label: str | None = None,
        service: str | None = None,
        key: str | None = None,
    ) -> dict:
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")
        
        api_key_data = self._store[key_id].copy()
        
        if label is not None:
            api_key_data["label"] = label
        
        if service is not None:
            normalized_service = validate_service_name(service)
            api_key_data["service"] = normalized_service
        
        if key is not None:
            validate_api_key_format(key, api_key_data["service"])
            api_key_data["key"] = key
        
        self._store[key_id] = api_key_data
        await self._save_store()
        
        return {
            "id": key_id,
            "label": api_key_data["label"],
            "service": api_key_data["service"],
        }