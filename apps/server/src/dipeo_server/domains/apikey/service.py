"""API Key management service."""

import json
import os
import uuid

from dipeo_core import BaseService, SupportsAPIKey

from config import BASE_DIR
from dipeo_server.shared.constants import VALID_LLM_SERVICES, normalize_service_name
from dipeo_server.shared.exceptions import APIKeyError, ValidationError


class APIKeyDomainService(BaseService, SupportsAPIKey):
    """Domain service for managing API keys that implements the SupportsAPIKey protocol."""

    VALID_SERVICES = VALID_LLM_SERVICES | {"notion"}

    def __init__(self, store_file: str | None = None):
        super().__init__()
        self.store_file = store_file or os.getenv(
            "API_KEY_STORE_FILE", f"{BASE_DIR}/files/apikeys.json"
        )
        self._store: dict[str, dict] = {}
        self._load_store()

    async def initialize(self) -> None:
        """Initialize the API key service."""
        # Service is already initialized in __init__
        pass

    def _load_store(self) -> None:
        """Load API keys from disk storage."""
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file) as f:
                    self._store.update(json.load(f))
            except (OSError, json.JSONDecodeError) as e:
                raise APIKeyError(f"Failed to load API key store: {e}")

    def _save_store(self) -> None:
        """Save API keys to disk storage."""
        try:
            with open(self.store_file, "w") as f:
                json.dump(self._store, f, indent=2)
        except OSError as e:
            raise APIKeyError(f"Failed to save API key store: {e}")

    def _validate_service(self, service: str) -> None:
        """Validate service name."""
        normalized_service = normalize_service_name(service)
        if normalized_service not in self.VALID_SERVICES:
            raise ValidationError(
                f"Invalid service. Must be one of: {self.VALID_SERVICES}"
            )

    def get_api_key(self, key_id: str) -> dict:
        """Get API key details by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")

        info = self._store[key_id]
        if isinstance(info, dict):
            return {
                "id": key_id,
                "label": info.get("label", key_id),
                "service": info.get("service", "unknown"),
                "key": info.get("key", ""),
            }
        return info

    def list_api_keys(self) -> list[dict]:
        result = []
        for key_id, info in self._store.items():
            # Handle both old and new format API keys
            if isinstance(info, dict) and "service" in info:
                result.append(
                    {
                        "id": key_id,
                        "label": info.get("label", key_id),
                        "service": info["service"],
                    }
                )
        return result

    def create_api_key(self, label: str, service: str, key: str) -> dict:
        """Create a new API key entry."""
        self.validate_required_fields(
            {"label": label, "service": service, "key": key},
            ["label", "service", "key"],
        )

        self._validate_service(service)

        key_id = f"APIKEY_{uuid.uuid4().hex[:6].upper()}"
        normalized_service = normalize_service_name(service)

        self._store[key_id] = {
            "label": label,
            "service": normalized_service,
            "key": key,
        }

        self._save_store()

        return {"id": key_id, "label": label, "service": normalized_service}

    def delete_api_key(self, key_id: str) -> None:
        """Delete an API key by ID."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")

        del self._store[key_id]
        self._save_store()

    def update_api_key(
        self,
        key_id: str,
        label: str | None = None,
        service: str | None = None,
        key: str | None = None,
    ) -> dict:
        """Update an existing API key."""
        if key_id not in self._store:
            raise APIKeyError(f"API key '{key_id}' not found")

        api_key_data = self._store[key_id].copy()

        if label is not None:
            api_key_data["label"] = label
        if service is not None:
            self._validate_service(service)
            api_key_data["service"] = normalize_service_name(service)
        if key is not None:
            api_key_data["key"] = key

        self._store[key_id] = api_key_data
        self._save_store()

        return {
            "id": key_id,
            "label": api_key_data["label"],
            "service": api_key_data["service"],
        }
