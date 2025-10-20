"""API key-related query resolvers."""

import asyncio
import logging

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import API_KEY_SERVICE, LLM_SERVICE
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import ApiKeyID
from dipeo.diagram_generated.enums import APIServiceType
from dipeo.diagram_generated.graphql.domain_types import DomainApiKeyType

logger = get_module_logger(__name__)


async def get_api_key(
    registry: ServiceRegistry, api_key_id: strawberry.ID
) -> DomainApiKeyType | None:
    """Get a single API key by ID."""
    try:
        apikey_service = registry.resolve(API_KEY_SERVICE)
        api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
        api_key_id_typed = ApiKeyID(str(api_key_id))

        for key_data in api_keys:
            if key_data.get("id") == str(api_key_id_typed):
                return DomainApiKeyType(
                    id=key_data["id"],
                    label=key_data["label"],
                    service=key_data["service"],
                    key=key_data.get("key", "***hidden***"),
                )

        return None

    except Exception as e:
        logger.error(f"Error fetching API key {api_key_id}: {e}")
        return None


async def get_api_keys(
    registry: ServiceRegistry, service: str | None = None
) -> list[DomainApiKeyType]:
    """List API keys, optionally filtered by service."""
    try:
        valid_services = {s.value for s in APIServiceType}

        apikey_service = registry.resolve(API_KEY_SERVICE)
        logger.debug(f"Got apikey_service: {apikey_service}")
        api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
        logger.debug(f"Got {len(api_keys)} API keys from service")

        domain_keys = []
        for key_data in api_keys:
            if key_data.get("service") not in valid_services:
                logger.debug(f"Skipping non-LLM service: {key_data.get('service')}")
                continue

            if service and key_data.get("service") != service:
                continue

            domain_keys.append(
                DomainApiKeyType(
                    id=key_data["id"],
                    label=key_data["label"],
                    service=key_data["service"],
                    key=key_data.get("key", "***hidden***"),
                )
            )

        return domain_keys

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return []


async def get_available_models(
    registry: ServiceRegistry, service: str, api_key_id: strawberry.ID
) -> list[str]:
    """Get available models for a given service and API key."""
    try:
        api_key_id_typed = ApiKeyID(str(api_key_id))
        api_key = await get_api_key(registry, api_key_id)
        if not api_key:
            logger.warning(f"API key not found: {api_key_id}")
            return []

        llm_service = registry.resolve(LLM_SERVICE)
        models = await llm_service.get_available_models(api_key_id_typed)

        return models

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return []
