"""Environment-based API Key Service infrastructure adapter."""

import os

from dipeo.domain.base import APIKeyError, BaseService, ValidationError
from dipeo.domain.constants import VALID_LLM_SERVICES, normalize_service_name
from dipeo.application.migration.compat_imports import APIKeyPort


class EnvironmentAPIKeyService(BaseService, APIKeyPort):
    """API Key service that reads from environment variables.
    
    This adapter allows applications to use environment variables for API key management,
    which is useful for CLI applications and containerized deployments.
    """

    VALID_SERVICES = VALID_LLM_SERVICES | {"notion"}

    ENV_VAR_MAPPING = {
        "openai": "OPENAI_API_KEY",
        "chatgpt": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "notion": "NOTION_API_KEY",
    }

    def __init__(self):
        super().__init__()
        self._cached_keys: dict[str, dict] = {}
        self._load_from_env()

    async def initialize(self) -> None:
        """Initialize the API key service."""
        pass

    def _load_from_env(self) -> None:
        """Load API keys from environment variables."""
        for service, env_var in self.ENV_VAR_MAPPING.items():
            api_key = os.getenv(env_var)
            if api_key:
                key_id = f"env_{service}"
                self._cached_keys[key_id] = {
                    "id": key_id,
                    "label": f"{service} (from {env_var})",
                    "service": service,
                    "key": api_key,
                }

    def _get_provider_from_model(self, model: str) -> str:
        """Determine provider from model name."""
        model_lower = model.lower()

        if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            return "openai"
        if "claude" in model_lower:
            return "anthropic"
        if "gemini" in model_lower:
            return "google"
        if "groq" in model_lower or "llama" in model_lower or "mixtral" in model_lower:
            return "groq"
        return "openai"

    def get_api_key(self, key_id: str) -> dict:
        """Get API key details by ID, service name, or model name."""
        if key_id in self._cached_keys:
            return self._cached_keys[key_id]

        if any(
            pattern in key_id.lower()
            for pattern in [
                "gpt",
                "claude",
                "gemini",
                "groq",
                "llama",
                "mixtral",
                "o1",
                "o3",
            ]
        ):
            provider = self._get_provider_from_model(key_id)
            normalized_service = normalize_service_name(provider)
        else:
            normalized_service = normalize_service_name(key_id)

        env_key_id = f"env_{normalized_service}"

        if env_key_id in self._cached_keys:
            return self._cached_keys[env_key_id]

        env_var = self.ENV_VAR_MAPPING.get(normalized_service)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                key_data = {
                    "id": env_key_id,
                    "label": f"{normalized_service} (from {env_var})",
                    "service": normalized_service,
                    "key": api_key,
                }
                self._cached_keys[env_key_id] = key_data
                return key_data

        raise APIKeyError(
            f"No API key found for '{key_id}'. "
            f"Please set the appropriate environment variable "
            f"({self.ENV_VAR_MAPPING.get(normalized_service, 'Unknown')})."
        )

    def list_api_keys(self) -> list[dict]:
        """List all available API keys from environment."""
        return list(self._cached_keys.values())

    def create_api_key(self, label: str, service: str, key: str) -> dict:
        """Create API key (not supported in environment mode)."""
        raise NotImplementedError(
            "Cannot create API keys in environment mode. "
            "Please set the appropriate environment variable instead."
        )

    def delete_api_key(self, key_id: str) -> None:
        """Delete API key (not supported in environment mode)."""
        raise NotImplementedError(
            "Cannot delete API keys in environment mode. "
            "Please unset the appropriate environment variable instead."
        )

    def update_api_key(
        self,
        key_id: str,
        label: str | None = None,
        service: str | None = None,
        key: str | None = None,
    ) -> dict:
        """Update API key (not supported in environment mode)."""
        raise NotImplementedError(
            "Cannot update API keys in environment mode. "
            "Please modify the appropriate environment variable instead."
        )

    def _validate_service(self, service: str) -> None:
        """Validate service name."""
        normalized_service = normalize_service_name(service)
        if normalized_service not in self.VALID_SERVICES:
            raise ValidationError(
                f"Invalid service. Must be one of: {self.VALID_SERVICES}"
            )