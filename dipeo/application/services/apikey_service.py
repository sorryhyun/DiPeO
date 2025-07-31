"""API Key orchestration service in the application layer."""

import json
import logging
from pathlib import Path

from dipeo.core import APIKeyError, BaseService
from dipeo.core.ports import APIKeyPort


class APIKeyService(BaseService, APIKeyPort):
    
    def __init__(self, file_path: Path | None = None):
        super().__init__()
        if file_path is None:
            file_path = Path.home() / ".dipeo" / "apikeys.json"
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._store: dict[str, dict] = {}
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"APIKeyService.__init__ called with file_path: {self.file_path}")
    
    async def initialize(self) -> None:
        self._store = await self._load_all()
        print(f"[APIKeyService] Loaded {len(self._store)} keys")
        self._logger.info(f"APIKeyService.initialize() - Loaded keys: {list(self._store.keys())}")
    
    async def _load_all(self) -> dict[str, dict]:
        """Load all API keys from file storage."""
        if not self.file_path.exists():
            return {}
        
        try:
            with open(self.file_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self._logger.error(f"Failed to load API keys from {self.file_path}: {e}")
            return {}
    
    async def _save_store(self) -> None:
        """Save all API keys to file storage."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._store, f, indent=2)
        except OSError as e:
            self._logger.error(f"Failed to save API keys to {self.file_path}: {e}")
            raise
    
    def get_api_key(self, key_id: str) -> dict:
        if key_id not in self._store:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"API key '{key_id}' not found. Available keys: {list(self._store.keys())}")
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


# API Key validation utilities

import uuid

from dipeo.core import ValidationError
from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name

VALID_SERVICES = VALID_LLM_SERVICES | {"notion"}


def validate_service_name(service: str) -> str:
    normalized = normalize_service_name(service)

    if normalized not in VALID_SERVICES:
        raise ValidationError(
            f"Invalid service '{service}'. Must be one of: {', '.join(VALID_SERVICES)}"
        )

    return normalized


def validate_api_key_format(key: str, service: str) -> None:
    if not key or not key.strip():
        raise ValidationError("API key cannot be empty")

    if service == "openai" and not key.startswith("sk-"):
        raise ValidationError("OpenAI API keys must start with 'sk-'")
    if service == "anthropic" and not key.startswith("sk-ant-"):
        raise ValidationError("Anthropic API keys must start with 'sk-ant-'")


def generate_api_key_id() -> str:
    return f"APIKEY_{uuid.uuid4().hex[:6].upper()}"


def format_api_key_info(key_id: str, info: dict) -> dict:
    if isinstance(info, dict):
        return {
            "id": key_id,
            "label": info.get("label", key_id),
            "service": info.get("service", "unknown"),
            "key": info.get("key", ""),
        }
    return info


def extract_api_key_summary(key_id: str, info: dict) -> dict:
    if isinstance(info, dict) and "service" in info:
        return {
            "id": key_id,
            "label": info.get("label", key_id),
            "service": info["service"],
        }
    return None