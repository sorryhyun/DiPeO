
import json
import os
import uuid

from dipeo.core import BaseService, SupportsAPIKey, APIKeyError, ValidationError
from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name, BASE_DIR


class APIKeyDomainService(BaseService, SupportsAPIKey):

    VALID_SERVICES = VALID_LLM_SERVICES | {"notion"}

    def __init__(self, store_file: str | None = None):
        super().__init__()
        # Default to project root files directory
        default_path = str(BASE_DIR / "files" / "apikeys.json")
        self.store_file = store_file or os.getenv("API_KEY_STORE_FILE", default_path)
        self._store: dict[str, dict] = {}
        self._load_store()

    async def initialize(self) -> None:
        pass

    def _load_store(self) -> None:
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file) as f:
                    self._store.update(json.load(f))
                print(
                    f"[APIKeyDomainService] Loaded {len(self._store)} keys from {self.store_file}"
                )
            except (OSError, json.JSONDecodeError) as e:
                raise APIKeyError(f"Failed to load API key store: {e}")
        else:
            print(f"[APIKeyDomainService] No store file found at {self.store_file}")

    def _save_store(self) -> None:
        try:
            with open(self.store_file, "w") as f:
                json.dump(self._store, f, indent=2)
        except OSError as e:
            raise APIKeyError(f"Failed to save API key store: {e}")

    def _validate_service(self, service: str) -> None:
        normalized_service = normalize_service_name(service)
        if normalized_service not in self.VALID_SERVICES:
            raise ValidationError(
                f"Invalid service. Must be one of: {self.VALID_SERVICES}"
            )

    def get_api_key(self, key_id: str) -> dict:
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
                        "label": info.get(
                            "label", key_id
                        ),  # Use key_id as default label
                        "service": info["service"],
                    }
                )
        return result

    def create_api_key(self, label: str, service: str, key: str) -> dict:
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
