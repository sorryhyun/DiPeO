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